import abc
import dataclasses

from ..models import BoardPlatform as BoardPlatformModel
from ..models import Position


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
