import uuid

from fastapi import FastAPI, WebSocket

app = FastAPI()


@app.get("/lobby")
async def root():
    pass


@app.websocket("/lobby/{lobby_id}/join")
async def websocket_endpoint(lobby_id: uuid.UUID, websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Message text was: {data}")
