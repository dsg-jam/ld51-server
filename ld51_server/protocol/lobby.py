import uuid
from typing import Literal, Union

from pydantic import BaseModel

from ..models import BoardPlatform, PlayerPiecePosition
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


class HostStartGamePayload(BaseModel):
    platform: BoardPlatform


class HostStartGameMessage(
    BaseMessage[Literal["host_start_game"], HostStartGamePayload]
):
    ...


class ServerStartGamePayload(BaseModel):
    platform: BoardPlatform
    pieces: list[PlayerPiecePosition]


class ServerStartGameMessage(
    BaseMessage[Literal["server_start_game"], ServerStartGamePayload]
):
    ...


LobbyMessagePayloadT = Union[
    ServerHelloPayload,
    PlayerJoinedPayload,
    HostStartGamePayload,
    ServerStartGamePayload,
]

LobbyMessageT = Union[
    ServerHelloMessage,
    PlayerJoinedMessage,
    HostStartGameMessage,
    ServerStartGameMessage,
]

__all__ = [
    ServerHelloPayload.__name__,
    ServerHelloMessage.__name__,
    PlayerJoinedPayload.__name__,
    PlayerJoinedMessage.__name__,
    HostStartGamePayload.__name__,
    HostStartGameMessage.__name__,
    ServerStartGamePayload.__name__,
    ServerStartGameMessage.__name__,
    "LobbyMessageT",
    "LobbyMessagePayloadT",
]
