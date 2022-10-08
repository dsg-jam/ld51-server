import asyncio
import dataclasses
import enum
import logging
import time
import uuid
from datetime import datetime
from typing import Any, Generic, Iterable, TypeVar

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
    ReadyForNextRoundPayload,
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

ROUND_DURATION = 10.0
ROUND_GRACE_PERIOD = ROUND_DURATION / 5.0
DURATION_PER_EVENT = 5.0

_WS_CLOSE_PROTOCOL_ERROR = 1002


class LobbyState(enum.IntEnum):
    EMPTY = enum.auto()
    LOBBY = enum.auto()
    GAME_ROUND_START = enum.auto()
    GAME_GET_PLAYER_MOVES = enum.auto()
    GAME_WAIT_PLAYER_READY = enum.auto()


_ItemT = TypeVar("_ItemT")


@dataclasses.dataclass()
class PlayerItemCollectorResult(Generic[_ItemT]):
    missing_player_ids: set[uuid.UUID]
    collected: dict[uuid.UUID, _ItemT]


class PlayerItemCollector(Generic[_ItemT]):
    _missing_player_ids: set[uuid.UUID]
    _moves_by_player: dict[uuid.UUID, _ItemT]
    _collected_all_players_ev: asyncio.Event

    def __init__(self, player_ids: Iterable[uuid.UUID]) -> None:
        self._missing_player_ids = set(player_ids)
        self._moves_by_player = {}
        self._collected_all_players_ev = asyncio.Event()

    def _check_done(self) -> None:
        if self._missing_player_ids:
            return
        self._collected_all_players_ev.set()

    def collect(self, player_id: uuid.UUID, item: _ItemT) -> None:
        self._moves_by_player[player_id] = item
        self._missing_player_ids.discard(player_id)
        self._check_done()

    def remove_player(self, player_id: uuid.UUID) -> None:
        self._missing_player_ids.discard(player_id)
        self._check_done()

    def _snapshot(self) -> PlayerItemCollectorResult[_ItemT]:
        return PlayerItemCollectorResult(
            missing_player_ids=self._missing_player_ids.copy(),
            collected=self._moves_by_player.copy(),
        )

    async def _wait(
        self, *, early_return_timestamp: float | None, grace_timeout: float
    ) -> PlayerItemCollectorResult[_ItemT]:
        try:
            await asyncio.wait_for(
                self._collected_all_players_ev.wait(), timeout=grace_timeout
            )
        except asyncio.TimeoutError:
            return self._snapshot()

        if early_return_timestamp is None:
            return self._snapshot()

        delay = early_return_timestamp - time.time()
        if delay > 0.0:
            # make sure we don't return before the expected time
            await asyncio.sleep(delay)

        return self._snapshot()

    async def wait_with_grace_period(
        self, *, delay: float, grace_period: float
    ) -> PlayerItemCollectorResult[_ItemT]:
        return await self._wait(
            early_return_timestamp=time.time() + delay,
            grace_timeout=delay + grace_period,
        )

    async def wait_up_to(self, *, timeout: float) -> PlayerItemCollectorResult[_ItemT]:
        return await self._wait(
            early_return_timestamp=None,
            grace_timeout=timeout,
        )


class Lobby:
    _id: uuid.UUID
    _state: LobbyState
    _created_at: datetime
    _host_player_id: uuid.UUID | None
    _player_by_id: dict[uuid.UUID, Player]

    _board: Board | None
    _round_number: int
    _game_loop_task: asyncio.Task[None] | None

    _player_moves_collector: PlayerItemCollector[list[TimelineEventAction]] | None
    _player_ready_collector: PlayerItemCollector[ReadyForNextRoundPayload] | None

    def __init__(self) -> None:
        self._id = uuid.uuid4()
        self._state = LobbyState.EMPTY
        self._created_at = datetime.now()
        self._host_player_id = None
        self._player_by_id = {}

        self._board = None
        self._round_number = 0
        self._game_loop_task = None

        self._player_moves_collector = None
        self._player_ready_collector = None

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
            self._state = LobbyState.LOBBY

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

        if collector := self._player_moves_collector:
            collector.remove_player(player.player_id)
        if collector := self._player_ready_collector:
            collector.remove_player(player.player_id)
        # TODO handle

    async def _on_player_msg(self, player: Player, msg: Message) -> None:
        error: ErrorPayload | None = None

        match msg.payload:
            case HostStartGamePayload():
                error = await self._msg_host_start_game(player, msg.payload)
            case PlayerMovesPayload():
                error = await self._msg_player_moves(player, msg.payload)
            case ReadyForNextRoundPayload():
                error = await self._msg_ready_for_next_round(player, msg.payload)
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

    async def _msg_ready_for_next_round(
        self, player: Player, payload: ReadyForNextRoundPayload
    ) -> ErrorPayload | None:
        if self._state != LobbyState.GAME_WAIT_PLAYER_READY:
            return ErrorPayload.invalid_lobby_state()

        assert self._board
        assert self._player_ready_collector

        self._player_ready_collector.collect(player.player_id, payload)

    async def _start_round(self) -> None:
        assert self._game_loop_task is None
        self._game_loop_task = asyncio.create_task(self.__game_loop(), name="game loop")

    async def __run_round(self) -> None:
        assert self._board is not None

        self._round_number += 1

        self._state = LobbyState.GAME_GET_PLAYER_MOVES
        self._player_moves_collector = PlayerItemCollector(self._player_by_id.keys())

        await self._broadcast(
            RoundStartMessage.from_payload(
                RoundStartPayload(
                    round_number=self._round_number,
                    round_duration=ROUND_DURATION,
                    board_state=self._board.get_pieces_model(),
                )
            )
        )

        # collect moves by all players
        collect_result = await self._player_moves_collector.wait_with_grace_period(
            delay=ROUND_DURATION, grace_period=ROUND_GRACE_PERIOD
        )
        # TODO: handle players that didn't submit in time. They should be considered disconnected
        self._player_moves_collector = None

        # execute moves
        timeline = self._board.perform_all_player_moves(collect_result.collected)
        estimated_animation_duration = len(timeline) * DURATION_PER_EVENT

        self._state = LobbyState.GAME_WAIT_PLAYER_READY
        self._player_ready_collector = PlayerItemCollector(self._player_by_id.keys())

        # TODO: do something when the game is over
        await self._broadcast(
            RoundResultMessage.from_payload(
                RoundResultPayload(
                    timeline=timeline,
                    game_over=self._board.get_game_over_model(),
                )
            )
        )

        collect_result = await self._player_ready_collector.wait_up_to(
            timeout=estimated_animation_duration
        )
        # TODO: take care of players that aren't ready
        self._player_ready_collector = None

    async def __game_loop(self) -> None:
        while True:
            try:
                await self.__run_round()
            # pylint: disable-next=broad-except
            except Exception:
                _LOGGER.exception(
                    "encountered exception during round %s", self._round_number
                )
