import asyncio
import enum
import logging
import uuid
from datetime import datetime
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from ..protocol import (
    BaseMessage,
    Message,
    PlayerJoinedMessage,
    PlayerJoinedPayload,
    RoundStartMessage,
    RoundStartPayload,
    ServerHelloMessage,
    ServerHelloPayload,
)
from .board import Board
from .player import Player

_LOGGER = logging.getLogger()


_WS_CLOSE_PROTOCOL_ERROR = 1002


class LobbyState(enum.IntEnum):
    EMPTY = enum.auto()
    LOBBY = enum.auto()
    IN_GAME = enum.auto()


class Lobby:
    _id: uuid.UUID
    _state: LobbyState
    _created_at: datetime
    _host_player_id: uuid.UUID | None
    _player_by_id: dict[uuid.UUID, Player]

    _board_state: Board | None
    _round_number: int

    def __init__(self) -> None:
        self._id = uuid.uuid4()
        self._state = LobbyState.EMPTY
        self._created_at = datetime.now()
        self._host_player_id = None
        self._player_by_id = {}

        self._board_state = None
        self._round_number = 0

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

            await self._on_player_msg(player, msg)

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
        # TODO handle

    async def _on_player_msg(self, player: Player, msg: Message) -> None:
        # TODO
        pass

    async def _do_one_round(self) -> None:
        assert self._board_state is not None
        self._round_number += 1
        round_duration = 10

        await self._broadcast(
            RoundStartMessage.from_payload(
                RoundStartPayload(
                    round_number=self._round_number,
                    round_duration=round_duration,
                    board_state=self._board_state.get_pieces_model(),
                )
            )
        )

    async def _round(self) -> None:
        # TODO
        round_duration = 10
        await self._broadcast(
            RoundStartMessage.from_payload(
                RoundStartPayload(
                    round_number=1, round_duration=round_duration, board_state=[]
                )
            )
        )

        await asyncio.sleep()
