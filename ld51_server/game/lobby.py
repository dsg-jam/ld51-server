import asyncio
import enum
import logging
import time
import uuid
from datetime import datetime
from typing import Any, Iterable

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from ..models import TimelineEventAction
from ..protocol import (
    BaseMessage,
    ErrorMessage,
    ErrorPayload,
    HostStartGamePayload,
    Message,
    PlayerJoinedMessage,
    PlayerJoinedPayload,
    PlayerMovesPayload,
    RoundResultMessage,
    RoundResultPayload,
    RoundStartMessage,
    RoundStartPayload,
    ServerHelloMessage,
    ServerHelloPayload,
    ServerStartGameMessage,
    ServerStartGamePayload,
)
from .board import Board, IllegalPlayerMoveError
from .board_platform import ClientDefinedPlatform
from .player import Player

_LOGGER = logging.getLogger()


_WS_CLOSE_PROTOCOL_ERROR = 1002


class LobbyState(enum.IntEnum):
    EMPTY = enum.auto()
    LOBBY = enum.auto()
    GAME_ROUND_START = enum.auto()
    GAME_GET_PLAYER_MOVES = enum.auto()
    GAME_WAIT_PLAYER_READY = enum.auto()


class PlayerMovesCollector:
    ValidatedMovesByPlayer = dict[uuid.UUID, list[TimelineEventAction]]

    _missing_player_ids: set[uuid.UUID]
    _moves_by_player: ValidatedMovesByPlayer
    _collected_all_players_ev: asyncio.Event
    _stop_collecting: bool

    def __init__(self, player_ids: Iterable[uuid.UUID]) -> None:
        self._missing_player_ids = set(player_ids)
        self._moves_by_player = {}
        self._collected_all_players_ev = asyncio.Event()
        self._stop_collecting = False

    def _check_done(self) -> None:
        if self._missing_player_ids:
            return
        self._collected_all_players_ev.set()

    def collect(
        self, player_id: uuid.UUID, validated_moves: list[TimelineEventAction]
    ) -> None:
        if self._stop_collecting:
            # ignore anything that comes in after the event is done
            return

        self._moves_by_player[player_id] = validated_moves
        self._missing_player_ids.discard(player_id)
        self._check_done()

    def remove_player(self, player_id: uuid.UUID) -> None:
        self._missing_player_ids.discard(player_id)
        self._check_done()

    async def _wait(
        self, *, early_return_timestamp: float, grace_timeout: float
    ) -> ValidatedMovesByPlayer:
        try:
            await asyncio.wait_for(
                self._collected_all_players_ev.wait(), timeout=grace_timeout
            )
        except asyncio.TimeoutError:
            return self._moves_by_player

        delay = time.time() - early_return_timestamp
        if delay > 0.0:
            # make sure we don't return before the expected time
            await asyncio.sleep(delay)

        return self._moves_by_player

    async def wait(
        self, *, timeout: float, grace_period: float
    ) -> ValidatedMovesByPlayer:
        try:
            return await self._wait(
                early_return_timestamp=time.time() + timeout,
                grace_timeout=timeout + grace_period,
            )
        finally:
            self._stop_collecting = True


class Lobby:
    _id: uuid.UUID
    _state: LobbyState
    _created_at: datetime
    _host_player_id: uuid.UUID | None
    _player_by_id: dict[uuid.UUID, Player]

    _board: Board | None
    _round_number: int

    _player_moves_collector: PlayerMovesCollector | None

    def __init__(self) -> None:
        self._id = uuid.uuid4()
        self._state = LobbyState.EMPTY
        self._created_at = datetime.now()
        self._host_player_id = None
        self._player_by_id = {}

        self._board = None
        self._round_number = 0

        self._player_moves_collector = None

    @property
    def lobby_id(self) -> uuid.UUID:
        return self._id

    def get_player_count(self) -> int:
        return len(self._player_by_id)

    def is_joinable(self) -> bool:
        match self._state:
            case LobbyState.EMPTY | LobbyState.LOBBY:
                return True
            case _:
                return False

    async def join_player(self, ws: WebSocket) -> Player:
        assert self.is_joinable

        await ws.accept()
        player = Player(ws)
        if self._host_player_id is None:
            self._host_player_id = player.player_id

        self._player_by_id[player.player_id] = player
        player.set_poll_task(
            asyncio.create_task(
                self.__player_poll_loop(player),
                name=f"poll task for player {player.player_id}",
            )
        )

        player_id = player.player_id
        await player.send_msg_silent(
            ServerHelloMessage.from_payload(
                ServerHelloPayload(
                    player_id=player_id, is_host=player_id == self._host_player_id
                )
            )
        )
        await self._broadcast(
            PlayerJoinedMessage.from_payload(PlayerJoinedPayload(player_id=player_id)),
            exclude_player_ids={player_id},
        )
        return player

    async def __player_poll_loop(self, player: Player) -> None:
        while True:
            try:
                msg = await player.receive_msg()
            except WebSocketDisconnect:
                break
            except ValidationError as exc:
                _LOGGER.warning(
                    "player %s sent an invalid message: %s", player.player_id, exc
                )
                await player.disconnect(
                    code=_WS_CLOSE_PROTOCOL_ERROR, reason="invalid message"
                )
                break

            try:
                await self._on_player_msg(player, msg)
            # we need broad exception handling here because otherwise the exception details will be lost entirely as there's no one above us to catch the exception
            # pylint: disable-next=broad-except
            except Exception:
                _LOGGER.exception(
                    "exception while handling message for player %s: %s",
                    player.player_id,
                    msg,
                )

        await self._on_player_disconnect(player)

    async def _broadcast(
        self,
        msg: BaseMessage[Any, Any],
        *,
        exclude_player_ids: set[uuid.UUID] | None = None,
    ) -> None:
        if exclude_player_ids:
            players = [
                player
                for player in self._player_by_id.values()
                if player.player_id not in exclude_player_ids
            ]
            if not players:
                return
        else:
            players = list(self._player_by_id.values())

        _LOGGER.debug("broadcasting message to %s player(s)", len(players))
        exceptions = await asyncio.gather(
            *(player.send_msg(msg) for player in players), return_exceptions=True
        )
        for player, exc in zip(players, exceptions):
            if exc is None:
                continue
            _LOGGER.warning(
                "failed to send message to player %s: %s", player.player_id, exc
            )

    async def _on_player_disconnect(self, player: Player) -> None:
        del self._player_by_id[player.player_id]
        player.set_poll_task(None)
        # TODO handle

    async def _on_player_msg(self, player: Player, msg: Message) -> None:
        error: ErrorPayload | None = None

        match msg.payload:
            case HostStartGamePayload():
                error = await self._msg_host_start_game(player, msg.payload)
            case PlayerMovesPayload():
                error = await self._msg_player_moves(player, msg.payload)
            case _:
                error = ErrorPayload.unhandled_message()

        if error is not None:
            await player.send_msg_silent(ErrorMessage.from_payload(error))

    async def _msg_host_start_game(
        self, player: Player, payload: HostStartGamePayload
    ) -> ErrorPayload | None:
        if player.player_id != self._host_player_id:
            return ErrorPayload.must_be_host()
        if self._state != LobbyState.LOBBY:
            return ErrorPayload.invalid_lobby_state()

        platform = ClientDefinedPlatform(payload.platform)
        self._state = LobbyState.GAME_ROUND_START
        self._board = Board(platform=platform)
        await self._broadcast(
            ServerStartGameMessage.from_payload(
                ServerStartGamePayload(
                    platform=platform.to_model(),
                    pieces=self._board.get_pieces_model(),
                )
            )
        )
        await self._start_round()
        return None

    async def _msg_player_moves(
        self, player: Player, payload: PlayerMovesPayload
    ) -> ErrorPayload | None:
        if self._state != LobbyState.GAME_GET_PLAYER_MOVES:
            return ErrorPayload.invalid_lobby_state()

        assert self._board
        assert self._player_moves_collector

        try:
            validated_moves = self._board.validate_player_moves(
                player.player_id, payload.moves
            )
        except IllegalPlayerMoveError as err:
            return ErrorPayload.illegal_player_move(
                piece_id=err.piece_id, message=err.message
            )

        self._player_moves_collector.collect(player.player_id, validated_moves)

    async def _start_round(self) -> None:
        asyncio.create_task(self.__run_round(), name="run round")
        # TODO maybe store this task somewhere?
        # TODO: wrap in exception catcher

    async def __run_round(self) -> None:
        assert self._board is not None

        self._round_number += 1
        round_duration = 10

        self._state = LobbyState.GAME_GET_PLAYER_MOVES
        self._player_moves_collector = PlayerMovesCollector(self._player_by_id.keys())
        await self._broadcast(
            RoundStartMessage.from_payload(
                RoundStartPayload(
                    round_number=self._round_number,
                    round_duration=round_duration,
                    board_state=self._board.get_pieces_model(),
                )
            )
        )

        # collect moves by all players
        moves_by_player = await self._player_moves_collector.wait(
            timeout=round_duration, grace_period=round_duration / 2.0
        )

        # execute moves
        timeline = self._board.perform_all_player_moves(moves_by_player)

        self._state = LobbyState.GAME_WAIT_PLAYER_READY
        await self._broadcast(
            RoundResultMessage.from_payload(
                RoundResultPayload(
                    timeline=timeline,
                    game_over=None,
                )
            )
        )

        # TODO wait for all players to be ready_for_next_round
