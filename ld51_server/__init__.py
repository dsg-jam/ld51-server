import uuid

from fastapi import FastAPI, HTTPException, WebSocket, status

from .models import GetLobbyInfoResponse, ListLobbiesResponse, Message

app = FastAPI(
    title="LD51 Server",
)


@app.get("/lobby", response_model=ListLobbiesResponse)
async def list_lobbies():
    pass


@app.get(
    "/lobby/{lobby_id}",
    response_model=GetLobbyInfoResponse,
    responses={status.HTTP_404_NOT_FOUND: {}},
)
async def get_lobby_info(lobby_id: uuid.UUID):
    raise HTTPException(status.HTTP_404_NOT_FOUND)


@app.post(
    "/lobby",
)
async def create_lobby():
    pass


@app.websocket("/lobby/{lobby_id}/join")
async def ws_join_lobby(lobby_id: uuid.UUID, websocket: WebSocket):
    await websocket.accept()
    while True:
        raw_data = await websocket.receive_json()
        msg = Message.parse_obj(raw_data)
        print(msg)
        await websocket.send_json(raw_data)
