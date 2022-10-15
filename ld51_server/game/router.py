import uuid

from fastapi import APIRouter, HTTPException, WebSocket, status

from ..models import (
    CreateLobbyResponse,
    GetLobbyInfoResponse,
    ListLobbiesResponse,
    LobbyInfo,
)
from .lobby import Lobby

__all__ = ["router"]

router = APIRouter(prefix="/lobby")

_LOBBIES_BY_ID: dict[uuid.UUID, Lobby] = {}


@router.get("", response_model=ListLobbiesResponse)
async def list_lobbies():
    lobbies: list[LobbyInfo] = []
    for lobby in _LOBBIES_BY_ID.values():
        lobbies.append(
            LobbyInfo(
                lobby_id=lobby.lobby_id,
                joinable=lobby.is_joinable(),
                players=lobby.get_player_count(),
            )
        )
    return ListLobbiesResponse.parse_obj(lobbies)


@router.get(
    "/{lobby_id}",
    response_model=GetLobbyInfoResponse,
    responses={status.HTTP_404_NOT_FOUND: {}},
)
async def get_lobby_info(lobby_id: uuid.UUID):
    lobby = _LOBBIES_BY_ID.get(lobby_id)
    if lobby is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    return GetLobbyInfoResponse(lobby_id=lobby.lobby_id)


@router.post(
    "",
    response_model=CreateLobbyResponse,
)
async def create_lobby():
    new_lobby = Lobby()
    _LOBBIES_BY_ID[new_lobby.lobby_id] = new_lobby
    return CreateLobbyResponse(lobby_id=new_lobby.lobby_id)


@router.websocket("/{lobby_id}/join")
async def ws_join_lobby(
    lobby_id: uuid.UUID, ws: WebSocket, *, session_id: uuid.UUID | None = None
):
    lobby = _LOBBIES_BY_ID.get(lobby_id)
    if lobby is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    if not lobby.is_joinable():
        raise HTTPException(status.HTTP_409_CONFLICT)

    # TODO handle reconnect with session_id
    player = await lobby.join_player(ws)
    await player.wait_until_done()
