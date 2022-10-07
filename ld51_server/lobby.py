import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect
from fastapi.encoders import jsonable_encoder
from pydantic import ValidationError

from .board import BoardState
from .protocol import (
    BaseMessage,
    Message,
    PlayerJoinedMessage,
    PlayerJoinedPayload,
    RoundStartMessage,
    ServerHelloMessage,
    ServerHelloPayload,
)

_LOGGER = logging.getLogger()

_WS_MODE = "text"

_WS_CLOSE_PROTOCOL_ERROR = 1002


class Player:
    _id: uuid.UUID
    _ws: WebSocket
    _poll_task: asyncio.Task[None] | None

    def __init__(self, ws: WebSocket) -> None:
        self._id = uuid.uuid4()
        self._ws = ws
        self._poll_task = None

    @property
    def player_id(self) -> uuid.UUID:
        return self._id

    def set_poll_task(self, poll_task: asyncio.Task[None] | None) -> None:
        if existing_poll_task := self._poll_task:
            existing_poll_task.cancel()

        self._poll_task = poll_task

    async def send_msg(self, msg: BaseMessage[Any, Any]) -> None:
        """
        Raises `WebSocketDisconnect`.
        """
        await self._ws.send_json(jsonable_encoder(msg), mode=_WS_MODE)

    async def send_msg_silent(self, msg: BaseMessage[Any, Any]) -> bool:
        try:
            await self.send_msg(msg)
        except WebSocketDisconnect:
            return False
        return True

    async def receive_msg(self) -> Message:
        """
        Raises `WebSocketDisconnect` or `ValidationError`.
        """
        raw_msg = await self._ws.receive_json(mode=_WS_MODE)
        return Message.parse_obj(raw_msg)

    async def disconnect(self, code: int, reason: str | None = None) -> None:
        await self._ws.close(code=code, reason=reason)
        self.set_poll_task(None)


class Lobby:
    _id: uuid.UUID
    _created_at: datetime
    _host_player_id: uuid.UUID | None
    _player_by_id: dict[uuid.UUID, Player]
    _board_state: BoardState | None

    def __init__(self) -> None:
        self._id = uuid.uuid4()
        self._created_at = datetime.now()
        self._host_player_id = None
        self._player_by_id = {}
        self._board_state = None

    @property
    def lobby_id(self) -> uuid.UUID:
        return self._id

    def get_player_count(self) -> int:
        return len(self._player_by_id)

    def is_joinable(self) -> bool:
        # TODO
        return self._board_state is None

    async def join_player(self, ws: WebSocket) -> None:
        await ws.accept()
        player = Player(ws)
        if self._host_player_id is None:
            self._host_player_id = player.player_id

        self._player_by_id[player.player_id] = player
        player.set_poll_task(asyncio.create_task(self.__player_poll_loop(player)))

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

        await player._poll_task

    async def __player_poll_loop(self, player: Player) -> None:
        while True:
            try:
                msg = await player.receive_msg()
            except WebSocketDisconnect:
                break
            except ValidationError:
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

    async def _round(self) -> None:
        # TODO
        round_duration = 10
        await self._broadcast(RoundStartMessage())
