import uuid
from typing import Literal, Union

from pydantic import BaseModel


class ServerHelloPayload(BaseModel):
    player_id: uuid.UUID
    is_host: bool


class ServerHelloMessage(BaseModel):
    type: Literal["server_hello"] = "server_hello"
    payload: ServerHelloPayload


class PlayerJoinedPayload(BaseModel):
    player_id: uuid.UUID


class PlayerJoinedMessage(BaseModel):
    type: Literal["player_joined"] = "player_joined"
    payload: PlayerJoinedPayload


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
