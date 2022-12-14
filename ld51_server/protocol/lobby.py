import uuid
from typing import Literal, Union

from pydantic import BaseModel, Field

from ..models import BoardPlatform, PlayerInfo, PlayerPiecePosition
from .base import BaseMessage


class ServerHelloPayload(BaseModel):
    session_id: uuid.UUID = Field(
        description="Private session id. This can be used to reconnect to the lobby in case of a disconnect."
    )
    is_host: bool
    player: PlayerInfo
    other_players: list[PlayerInfo] = Field(
        description="Other players that are already in the lobby."
    )


class ServerHelloMessage(BaseMessage[Literal["server_hello"], ServerHelloPayload]):
    ...


class PlayerJoinedPayload(BaseModel):
    player: PlayerInfo


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
    players: list[PlayerInfo]
    pieces: list[PlayerPiecePosition]
    round_start_in: float = Field(
        description="Time until the first round starts in seconds.", ge=0.0
    )


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
