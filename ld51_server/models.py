import enum
import uuid

from pydantic import BaseModel


class Direction(str, enum.Enum):
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"


class PieceAction(str, enum.Enum):
    MOVE_UP = "move_up"
    MOVE_DOWN = "move_down"
    MOVE_LEFT = "move_left"
    MOVE_RIGHT = "move_right"


class Position(BaseModel):
    x: int
    y: int


class PlayerPiecePosition(BaseModel):
    player_id: uuid.UUID
    piece_id: uuid.UUID
    position: Position


class RoundStartMessagePayload(BaseModel):
    round_number: int
    round_duration: float
    board_state: list[PlayerPiecePosition]
