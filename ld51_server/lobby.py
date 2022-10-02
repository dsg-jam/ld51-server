import uuid
from datetime import datetime

from fastapi import WebSocket


class Player:
    _id: uuid.UUID
    _ws: WebSocket

    def __init__(self, ws: WebSocket) -> None:
        self._id = uuid.uuid4()
        self._ws = ws

    @property
    def player_id(self) -> uuid.UUID:
        return self._id


class Lobby:
    _id: uuid.UUID
    _created_at: datetime
    _host_player_id: uuid.UUID | None
    _player_by_id: dict[uuid.UUID, Player]

    def __init__(self) -> None:
        self._id = uuid.uuid4()
        self._created_at = datetime.now()
        self._host_player_id = None
        self._player_by_id = {}

    @property
    def lobby_id(self) -> uuid.UUID:
        return self._id

    def get_player_count(self) -> int:
        return len(self._player_by_id)

    def is_joinable(self) -> bool:
        # TODO
        return True

    async def join_player(self, ws: WebSocket) -> None:
        await ws.accept()
        player = Player(ws)
        if self._host_player_id is None:
            self._host_player_id = player.player_id

        self._player_by_id[player.player_id] = player
        # TODO: send hello to all other players
