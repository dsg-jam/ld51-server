import enum
import uuid

from pydantic import BaseModel, Field


class Direction(str, enum.Enum):
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"

    def get_opposite(self) -> "Direction":
        match self:
            case self.UP:
                return self.DOWN
            case self.DOWN:
                return self.UP
            case self.LEFT:
                return self.RIGHT
            case self.RIGHT:
                return self.LEFT
        raise NotImplementedError


class PieceAction(str, enum.Enum):
    NO_ACTION = "no_action"
    MOVE_UP = "move_up"
    MOVE_DOWN = "move_down"
    MOVE_LEFT = "move_left"
    MOVE_RIGHT = "move_right"

    def as_direction(self) -> Direction | None:
        match self:
            case self.NO_ACTION:
                return None
            case self.MOVE_UP:
                return Direction.UP
            case self.MOVE_DOWN:
                return Direction.DOWN
            case self.MOVE_LEFT:
                return Direction.LEFT
            case self.MOVE_RIGHT:
                return Direction.RIGHT
        raise NotImplementedError


class Position(BaseModel):
    x: int
    y: int

    class Config:
        frozen = True

    def offset_in_direction(
        self, direction: Direction, *, steps: int = 1
    ) -> "Position":
        x, y = self.x, self.y
        match direction:
            case Direction.UP:
                y -= steps
            case Direction.DOWN:
                y += steps
            case Direction.LEFT:
                x -= steps
            case Direction.RIGHT:
                x += steps
        return type(self)(x=x, y=y)


class PlayerPiecePosition(BaseModel):
    player_id: uuid.UUID
    piece_id: uuid.UUID
    position: Position


class PlayerMove(BaseModel):
    piece_id: uuid.UUID
    action: PieceAction


class PlayerInfo(BaseModel):
    id: uuid.UUID = Field(description="Globally unique identifier of the player")
    number: int = Field(
        description="Human-friendly identifier of the player. Only unique within the session",
        ge=1,
    )


class GameOver(BaseModel):
    winner_player_id: uuid.UUID | None


__all__ = [
    "Direction",
    "PieceAction",
    "Position",
    "PlayerPiecePosition",
    "PlayerMove",
    "PlayerInfo",
    "GameOver",
]
