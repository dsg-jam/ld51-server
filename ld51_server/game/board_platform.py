import abc
import dataclasses

from ..models import BoardPlatform as BoardPlatformModel
from ..models import BoardPlatformTile, Position


class BoardPlatformABC(abc.ABC):
    @abc.abstractmethod
    def is_position_on_board(self, pos: Position) -> bool:
        ...

    @abc.abstractmethod
    def to_model(self) -> BoardPlatformModel:
        ...


class InfiniteBoardPlatform(BoardPlatformABC):
    def is_position_on_board(self, pos: Position) -> bool:
        return True

    def to_model(self) -> BoardPlatformModel:
        raise NotImplementedError


@dataclasses.dataclass()
class SimpleRectangleBoardPlatform(BoardPlatformABC):
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


class ClientDefinedPlatform(BoardPlatformABC):
    _tile_by_pos: dict[Position, BoardPlatformTile]

    def __init__(self, model: BoardPlatformModel) -> None:
        self._tile_by_pos = {tile.position: tile for tile in model.tiles}

    def is_position_on_board(self, pos: Position) -> bool:
        try:
            tile = self._tile_by_pos[pos]
        except KeyError:
            return False

        return tile.tile_type.is_off_board()

    def to_model(self) -> BoardPlatformModel:
        return BoardPlatformModel(tiles=list(self._tile_by_pos.values()))
