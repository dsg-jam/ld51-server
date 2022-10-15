import uuid

from fastapi import APIRouter, Depends, HTTPException, WebSocket, status
from pydantic import BaseModel

from .lobby_manager import LobbyManager, get_lobby_manager

__all__ = ["router"]

router = APIRouter(prefix="/lobby")


class LobbyInfo(BaseModel):
    lobby_id: uuid.UUID
    joinable: bool
    players: int


class ListLobbiesResponse(BaseModel):
    __root__: list[LobbyInfo]


@router.get("", response_model=ListLobbiesResponse)
async def list_lobbies(*, lobby_manager: LobbyManager = Depends(get_lobby_manager)):
    lobbies: list[LobbyInfo] = []
    for lobby in lobby_manager.iter_lobbies():
        lobbies.append(
            LobbyInfo(
                lobby_id=lobby.lobby_id,
                joinable=lobby.is_joinable(),
                players=lobby.get_player_count(),
            )
        )
    return ListLobbiesResponse.parse_obj(lobbies)


class GetLobbyInfoResponse(BaseModel):
    lobby_id: uuid.UUID


@router.get(
    "/{lobby_id}",
    response_model=GetLobbyInfoResponse,
    responses={status.HTTP_404_NOT_FOUND: {}},
)
async def get_lobby_info(
    lobby_id: uuid.UUID, *, lobby_manager: LobbyManager = Depends(get_lobby_manager)
):
    lobby = lobby_manager.get_lobby(lobby_id)
    if lobby is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    return GetLobbyInfoResponse(lobby_id=lobby.lobby_id)


class CreateLobbyResponse(BaseModel):
    lobby_id: uuid.UUID


@router.post(
    "",
    response_model=CreateLobbyResponse,
)
async def create_lobby(*, lobby_manager: LobbyManager = Depends(get_lobby_manager)):
    new_lobby = await lobby_manager.create_lobby()
    return CreateLobbyResponse(lobby_id=new_lobby.lobby_id)


@router.websocket("/{lobby_id}/join")
async def ws_join_lobby(
    lobby_id: uuid.UUID,
    ws: WebSocket,
    *,
    session_id: uuid.UUID | None = None,
    lobby_manager: LobbyManager = Depends(get_lobby_manager)
):
    lobby = lobby_manager.get_lobby(lobby_id)
    if lobby is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    # TODO handle reconnect with session_id
    assert session_id is None

    if not lobby.is_joinable():
        raise HTTPException(status.HTTP_409_CONFLICT)

    player = await lobby.join_player(ws)
    await player.wait_until_done()
