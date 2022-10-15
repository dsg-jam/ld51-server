import uuid
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..game.lobby_manager import LobbyManager, get_lobby_manager
from ..models import PlayerInfo

router = APIRouter(prefix="/lobby", tags=["dev-tools"])


class LobbyInfo(BaseModel):
    lobby_id: uuid.UUID
    created_at: datetime
    joinable: bool
    state: str
    players: list[PlayerInfo]


class ListLobbiesResponse(BaseModel):
    __root__: list[LobbyInfo]


@router.get("/list", response_model=ListLobbiesResponse)
async def list_lobbies(*, lobby_manager: LobbyManager = Depends(get_lobby_manager)):
    lobbies: list[LobbyInfo] = []
    for lobby in lobby_manager.iter_lobbies():
        lobbies.append(
            LobbyInfo(
                lobby_id=lobby.lobby_id,
                created_at=lobby.created_at,
                joinable=lobby.is_joinable(),
                state=lobby.get_lobby_state_repr(),
                players=lobby.get_player_info_models(),
            )
        )
    return ListLobbiesResponse.parse_obj(lobbies)
