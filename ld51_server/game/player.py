import asyncio
import logging
import uuid
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect
from fastapi.encoders import jsonable_encoder

from ..models import PlayerInfo
from ..protocol import BaseMessage, Message

_LOGGER = logging.getLogger()

_WS_MODE = "text"


class Player:
    _id: uuid.UUID
    _number: int
    _session_id: uuid.UUID
    _ws: WebSocket
    _poll_task: asyncio.Task[None] | None

    def __init__(self, ws: WebSocket, *, player_number: int) -> None:
        self._id = uuid.uuid4()
        self._number = player_number
        self._session_id = uuid.uuid4()
        self._ws = ws
        self._poll_task = None

    @property
    def player_id(self) -> uuid.UUID:
        return self._id

    @property
    def player_number(self) -> int:
        return self._number

    @property
    def session_id(self) -> uuid.UUID:
        return self._session_id

    def replace_ws(self, ws: WebSocket) -> None:
        self._ws = ws

    def get_player_info_model(self) -> PlayerInfo:
        return PlayerInfo(
            id=self._id,
            number=self._number,
        )

    async def wait_until_done(self) -> None:
        if self._poll_task is None:
            return
        try:
            await self._poll_task
        except asyncio.CancelledError:
            pass

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

    async def disconnect_silent(self, code: int, reason: str | None = None) -> bool:
        try:
            await self.disconnect(code, reason)
        except WebSocketDisconnect:
            return False
        return True
