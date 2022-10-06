import dataclasses
import enum
import uuid
from typing import Iterator

from ld51_server.board import BoardState, PieceInformation, SimpleRectangleBoardPlatform
from ld51_server.models import PieceAction, PlayerMove, Position

DUMMY_PLAYER_ID = uuid.UUID("00000000-0000-0000-0000-000000000000")

C_COMMENT = "#"
C_END_OF_LINE = "|"


class BoardCell(str, enum.Enum):
    EMPTY = " "
    PIECE = "o"
    MOVE_UP = "^"
    MOVE_DOWN = "v"
    MOVE_LEFT = "<"
    MOVE_RIGHT = ">"

    def has_piece(self) -> bool:
        return self != self.EMPTY

    def to_player_move(self, piece_id: uuid.UUID) -> PlayerMove | None:
        match self:
            case self.EMPTY | self.PIECE:
                return None
            case self.MOVE_UP:
                return PlayerMove(piece_id=piece_id, action=PieceAction.MOVE_UP)
            case self.MOVE_DOWN:
                return PlayerMove(piece_id=piece_id, action=PieceAction.MOVE_DOWN)
            case self.MOVE_LEFT:
                return PlayerMove(piece_id=piece_id, action=PieceAction.MOVE_LEFT)
            case self.MOVE_RIGHT:
                return PlayerMove(piece_id=piece_id, action=PieceAction.MOVE_RIGHT)
            case _:
                raise NotImplementedError


@dataclasses.dataclass()
class BoardStateAndMoves:
    board_state: BoardState
    player_moves: list[PlayerMove]


@dataclasses.dataclass()
class AsciiStateAndMoves:
    board_grid: list[list[BoardCell]]
    width: int
    height: int

    @classmethod
    def parse(cls, raw: str):
        state = cls(board_grid=[], width=0, height=0)
        for raw_line in raw.splitlines():
            if raw_line.startswith(C_COMMENT):
                continue
            state.height += 1
            row: list[BoardCell] = []
            for raw_char in raw_line:
                if raw_char == C_END_OF_LINE:
                    break
                cell = BoardCell(raw_char)
                row.append(cell)

            state.width = max(state.width, len(row))
            state.board_grid.append(row)

        state._normalize()
        return state

    @classmethod
    def from_board_state(cls, board_state: BoardState, width: int, height: int):
        state = cls(board_grid=[], width=width, height=height)
        state._normalize()

        for y in range(height):
            for x in range(width):
                piece = board_state.get_piece_at_position(Position(x=x, y=y))
                if piece is not None:
                    state.board_grid[y][x] = BoardCell.PIECE

        return state

    def _normalize(self) -> None:
        for _ in range(self.height - len(self.board_grid)):
            self.board_grid.append([])

        for line in self.board_grid:
            for _ in range(self.width - len(line)):
                line.append(BoardCell.EMPTY)

    def _iter_rendered_lines(self, *, with_border: bool = True) -> Iterator[str]:
        for row in self.board_grid:
            content = "".join(pos.value for pos in row)
            if with_border:
                yield f"|{content}|"
            else:
                yield content

    def render(self, *, with_border: bool = True) -> str:
        return "\n".join(self._iter_rendered_lines(with_border=with_border))

    def to_board_state_and_moves(self) -> BoardStateAndMoves:
        state = BoardStateAndMoves(board_state=BoardState(), player_moves=[])
        state.board_state._platform = SimpleRectangleBoardPlatform(
            top_left=Position(x=0, y=0),
            bottom_right=Position(x=self.width - 1, y=self.height - 1),
        )
        for y, row in enumerate(self.board_grid):
            for x, cell in enumerate(row):
                piece_id = uuid.uuid5(DUMMY_PLAYER_ID, f"{x}:{y}")
                if cell.has_piece():
                    state.board_state._piece_by_position[
                        Position(x=x, y=y)
                    ] = PieceInformation(player_id=DUMMY_PLAYER_ID, piece_id=piece_id)
                if move := cell.to_player_move(piece_id):
                    state.player_moves.append(move)

        return state
