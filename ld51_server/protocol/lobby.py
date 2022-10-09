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
    # TODO this doesn't actually need to be here because the round start message will also contain the piece positions
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
    "ServerHelloPayload",
    "ServerHelloMessage",
    "PlayerJoinedPayload",
    "PlayerJoinedMessage",
    "HostStartGamePayload",
    "HostStartGameMessage",
    "ServerStartGamePayload",
    "ServerStartGameMessage",
    "LobbyMessageT",
    "LobbyMessagePayloadT",
]
