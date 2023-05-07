import abc
import dataclasses
from random import Random
from typing import Iterator

from ..models import BoardPlatform as BoardPlatformModel
from ..models import BoardPlatformTile, Position


class BoardPlatformABC(abc.ABC):
    @abc.abstractmethod
    def is_position_on_board(self, pos: Position) -> bool:
        ...

    @abc.abstractmethod
    def to_model(self) -> BoardPlatformModel:
        ...

    @abc.abstractmethod
    def on_board_positions(self) -> int | None:
        """Number of available positions or `None` if unlimited."""

    @abc.abstractmethod
    def get_random_position_on_board(
        self, rng: Random, *, exclude: set[Position] | None = None
    ) -> Position | None:
        ...


class InfiniteBoardPlatform(BoardPlatformABC):
    def is_position_on_board(self, pos: Position) -> bool:
        return True

    def to_model(self) -> BoardPlatformModel:
        raise NotImplementedError

    def on_board_positions(self) -> None:
        return None

    def get_random_position_on_board(
        self, rng: Random, *, exclude: set[Position] | None = None
    ) -> Position:
        _bits = 16

        center = rng.getrandbits(_bits)
        while True:
            x = rng.getrandbits(_bits) - center
            y = rng.getrandbits(_bits) - center
            pos = Position(x=x, y=y)
            if exclude and pos in exclude:
                continue
            return pos


@dataclasses.dataclass()
class RectangleBoardPlatform(BoardPlatformABC):
    top_left: Position
    bottom_right: Position

    @property
    def min_x(self) -> int:
        return self.top_left.x

    @property
    def min_y(self) -> int:
        return self.top_left.y

    @property
    def max_x(self) -> int:
        return self.bottom_right.x

    @property
    def max_y(self) -> int:
        return self.bottom_right.y

    def is_position_on_board(self, pos: Position) -> bool:
        return self.min_x <= pos.x <= self.max_x and self.min_y <= pos.y <= self.max_y

    def to_model(self) -> BoardPlatformModel:
        raise NotImplementedError

    def on_board_positions(self) -> int:
        width = self.max_x - self.min_x + 1
        height = self.max_y - self.min_y + 1
        return width * height

    def _iter_positions(self) -> Iterator[Position]:
        for x in range(self.min_x, self.max_x + 1):
            for y in range(self.min_y, self.max_y + 1):
                yield Position(x=x, y=y)

    def get_random_position_on_board(
        self, rng: Random, *, exclude: set[Position] | None = None
    ) -> Position | None:
        if not exclude:
            x = rng.randint(self.min_x, self.max_x)
            y = rng.randint(self.min_y, self.max_y)
            return Position(x=x, y=y)

        choices = tuple(pos for pos in self._iter_positions() if pos not in exclude)
        if not choices:
            return None
        return rng.choice(choices)


class ClientDefinedPlatform(BoardPlatformABC):
    _tile_by_pos: dict[Position, BoardPlatformTile]
    _on_board_positions: set[Position]

    def __init__(self, model: BoardPlatformModel) -> None:
        self._tile_by_pos = {tile.position: tile for tile in model.tiles}
        self._on_board_positions = {
            tile.position for tile in model.tiles if not tile.tile_type.is_off_board()  # type: ignore
        }

    def is_position_on_board(self, pos: Position) -> bool:
        return pos in self._on_board_positions

    def to_model(self) -> BoardPlatformModel:
        return BoardPlatformModel(tiles=list(self._tile_by_pos.values()))

    def on_board_positions(self) -> int:
        return len(self._on_board_positions)

    def get_random_position_on_board(
        self, rng: Random, *, exclude: set[Position] | None = None
    ) -> Position | None:
        if exclude is None:
            exclude = set()
        choices = tuple(pos for pos in self._on_board_positions if pos not in exclude)
        if not choices:
            return None
        return rng.choice(choices)
