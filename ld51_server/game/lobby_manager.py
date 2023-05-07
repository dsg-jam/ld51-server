import asyncio
import uuid
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Iterator

from .join_code import JoinCodeGenerator
from .lobby import Lobby

_GC_RUN_INTERVAL = 5 * 60
_MIN_LOBBY_LIFESPAN = timedelta(minutes=5)
_MAX_LOBBY_LIFESPAN = timedelta(hours=6)


class LobbyManager:
    _join_code_gen: JoinCodeGenerator
    _lobbies_by_id: dict[uuid.UUID, Lobby]
    _ids_by_join_code: dict[str, uuid.UUID]
    _garbage_collector: asyncio.Task[None] | None

    def __init__(self) -> None:
        self._join_code_gen = JoinCodeGenerator()
        self._lobbies_by_id = {}
        self._ids_by_join_code = {}
        self._garbage_collector = None

    def iter_lobbies(self) -> Iterator[Lobby]:
        return iter(self._lobbies_by_id.values())

    def get_lobby(self, lobby_id: uuid.UUID) -> Lobby | None:
        return self._lobbies_by_id.get(lobby_id)

    def get_lobby_by_join_code(self, code: str) -> Lobby | None:
        try:
            lobby_id = self._ids_by_join_code[code]
        except KeyError:
            return None
        return self.get_lobby(lobby_id)

    def _create_join_code(self) -> str:
        while True:
            code = self._join_code_gen.generate()
            if self.get_lobby_by_join_code(code) is None:
                return code

            # we got a join code conflict, start using longer ones
            self._join_code_gen.bump_len()

    async def create_lobby(self) -> Lobby:
        new_lobby = Lobby()
        new_lobby.join_code = self._create_join_code()

        self._lobbies_by_id[new_lobby.lobby_id] = new_lobby
        self._ids_by_join_code[new_lobby.join_code] = new_lobby.lobby_id

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

    async def __gc_run_once(self) -> bool:
        lobbies_to_destroy: list[uuid.UUID] = []
        for lobby_id, lobby in self._lobbies_by_id.items():
            if self.__gc_check_lobby(lobby):
                lobbies_to_destroy.append(lobby_id)

        for lobby_id in lobbies_to_destroy:
            lobby = self._lobbies_by_id.pop(lobby_id)
            await lobby.shutdown()

        return bool(lobbies_to_destroy)

    async def __gc_loop(self) -> None:
        while True:
            await asyncio.sleep(_GC_RUN_INTERVAL)
            cleaned = await self.__gc_run_once()
            if cleaned:
                # since we removed some dead lobbies, reset the join code length
                self._join_code_gen.reset_len()


@lru_cache()
def get_lobby_manager() -> LobbyManager:
    return LobbyManager()
