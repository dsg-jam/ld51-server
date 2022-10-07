import enum

from pydantic import BaseModel, Field

from .general import Position


class BoardPlatformTileType(str, enum.Enum):
    VOID = "void"
    FLOOR = "floor"


class BoardPlatformTile(BaseModel):
    position: Position
    texture_id: str = Field(examples=["grass", "sand"])
    tile_type: BoardPlatformTileType


class BoardPlatform(BaseModel):
    tiles: list[BoardPlatformTile]


__all__ = [
    BoardPlatformTileType.__name__,
    BoardPlatformTile.__name__,
    BoardPlatform.__name__,
]
