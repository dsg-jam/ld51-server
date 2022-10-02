import uuid

from pydantic import BaseModel


class LobbyInfo(BaseModel):
    lobby_id: uuid.UUID
    joinable: bool
    players: int


class ListLobbiesResponse(BaseModel):
    __root__: list[LobbyInfo]


class GetLobbyInfoResponse(BaseModel):
    lobby_id: uuid.UUID


class CreateLobbyResponse(BaseModel):
    lobby_id: uuid.UUID


__all__ = [
    LobbyInfo.__name__,
    ListLobbiesResponse.__name__,
    GetLobbyInfoResponse.__name__,
    CreateLobbyResponse.__name__,
]
