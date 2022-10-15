import asyncio
import uuid
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Iterator

from .lobby import Lobby

_GC_RUN_INTERVAL = 5 * 60
_MIN_LOBBY_LIFESPAN = timedelta(minutes=5)
_MAX_LOBBY_LIFESPAN = timedelta(hours=6)


class LobbyManager:
    _lobbies_by_id: dict[uuid.UUID, Lobby]
    _garbage_collector: asyncio.Task[None] | None

    def __init__(self) -> None:
        self._lobbies_by_id = {}
        self._garbage_collector = None

    def iter_lobbies(self) -> Iterator[Lobby]:
        return iter(self._lobbies_by_id.values())

    def get_lobby(self, lobby_id: uuid.UUID) -> Lobby | None:
        return self._lobbies_by_id.get(lobby_id)

    async def create_lobby(self) -> Lobby:
        new_lobby = Lobby()
        self._lobbies_by_id[new_lobby.lobby_id] = new_lobby

        if self._garbage_collector is None:
            self._garbage_collector = asyncio.create_task(
                self.__gc_loop(), name="lobby garbage collector"
            )

        return new_lobby

    def __gc_check_lobby(self, lobby: Lobby) -> bool:
        lifespan = datetime.now() - lobby.created_at
        if lifespan >= _MAX_LOBBY_LIFESPAN:
            return True
        if lifespan < _MIN_LOBBY_LIFESPAN:
            return False

        return lobby.get_player_count() == 0

    async def __gc_run_once(self) -> None:
        lobbies_to_destroy: list[uuid.UUID] = []
        for lobby_id, lobby in self._lobbies_by_id.items():
            if self.__gc_check_lobby(lobby):
                lobbies_to_destroy.append(lobby_id)

        for lobby_id in lobbies_to_destroy:
            lobby = self._lobbies_by_id.pop(lobby_id)
            await lobby.shutdown()

    async def __gc_loop(self) -> None:
        while True:
            await asyncio.sleep(_GC_RUN_INTERVAL)
            await self.__gc_run_once()


@lru_cache()
def get_lobby_manager() -> LobbyManager:
    return LobbyManager()
