import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, WebSocket, status
from pydantic import BaseModel

from ..protocol import ws_close_code
from .lobby_manager import LobbyManager, get_lobby_manager

__all__ = ["router"]

_LOGGER = logging.getLogger(__name__)

router = APIRouter(prefix="/lobby")


class GetLobbyInfoResponse(BaseModel):
    lobby_id: uuid.UUID
    join_code: str | None


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
    return GetLobbyInfoResponse(lobby_id=lobby.lobby_id, join_code=lobby.join_code)


class CreateLobbyResponse(BaseModel):
    lobby_id: uuid.UUID
    join_code: str | None


@router.post(
    "",
    response_model=CreateLobbyResponse,
)
async def create_lobby(*, lobby_manager: LobbyManager = Depends(get_lobby_manager)):
    new_lobby = await lobby_manager.create_lobby()
    _LOGGER.debug(
        "created new lobby %s with join code %s",
        new_lobby.lobby_id,
        new_lobby.join_code,
    )
    return CreateLobbyResponse(
        lobby_id=new_lobby.lobby_id, join_code=new_lobby.join_code
    )


@router.websocket("/{id_or_code}/join")
async def ws_join_lobby(
    id_or_code: uuid.UUID | str,
    ws: WebSocket,
    *,
    session_id: uuid.UUID | None = None,
    lobby_manager: LobbyManager = Depends(get_lobby_manager)
):
    if isinstance(id_or_code, uuid.UUID):
        lobby = lobby_manager.get_lobby(id_or_code)
    else:
        lobby = lobby_manager.get_lobby_by_join_code(id_or_code)

    if lobby is None:
        await ws.close(**ws_close_code.LOBBY_NOT_FOUND)
        raise HTTPException(status.HTTP_404_NOT_FOUND)

    _LOGGER.debug("joining lobby %s with session id %s", lobby.lobby_id, session_id)

    if session_id is None:
        if not lobby.is_joinable():
            await ws.close(**ws_close_code.LOBBY_NOT_JOINABLE)
            raise HTTPException(status.HTTP_409_CONFLICT)

        player = await lobby.join_player(ws)
    else:
        player = await lobby.reconnect_player(ws, session_id)
        if player is None:
            await ws.close(**ws_close_code.LOBBY_SESSION_EXPIRED)
            raise HTTPException(status.HTTP_410_GONE)

    await player.wait_until_done()
