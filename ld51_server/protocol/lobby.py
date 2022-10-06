import uuid
from typing import Literal, Union

from pydantic import BaseModel

from .base import BaseMessage


class ServerHelloPayload(BaseModel):
    player_id: uuid.UUID
    is_host: bool


class ServerHelloMessage(BaseMessage[Literal["server_hello"], ServerHelloPayload]):
    ...


class PlayerJoinedPayload(BaseModel):
    player_id: uuid.UUID


class PlayerJoinedMessage(BaseMessage[Literal["player_joined"], PlayerJoinedPayload]):
    ...


LobbyMessageT = Union[ServerHelloMessage, PlayerJoinedMessage]
LobbyMessagePayloadT = Union[
    ServerHelloPayload,
    PlayerJoinedPayload,
]

__all__ = [
    ServerHelloPayload.__name__,
    ServerHelloMessage.__name__,
    PlayerJoinedPayload.__name__,
    PlayerJoinedMessage.__name__,
    "LobbyMessageT",
    "LobbyMessagePayloadT",
]
