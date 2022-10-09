import enum

from pydantic import BaseModel, Field

from .general import Position


class BoardPlatformTileType(str, enum.Enum):
    VOID = "void"
    FLOOR = "floor"

    def is_off_board(self) -> bool:
        return self == self.VOID


class BoardPlatformTile(BaseModel):
    position: Position
    texture_id: str = Field(examples=["grass", "sand"])
    tile_type: BoardPlatformTileType


class BoardPlatform(BaseModel):
    tiles: list[BoardPlatformTile]


__all__ = [
    "BoardPlatformTileType",
    "BoardPlatformTile",
    "BoardPlatform",
]
