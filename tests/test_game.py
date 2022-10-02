import dataclasses
import random
import uuid
from pathlib import Path

import pytest

from ld51_server.board import BoardState, PieceInformation
from ld51_server.models import PieceAction, PlayerMove, Position

from . import DATA_DIR

BOARD_STATES_DIR = DATA_DIR / "board_states"


@dataclasses.dataclass()
class Case:
    width: int
    height: int

    board_state: BoardState
    player_moves: list[PlayerMove]


def case_from_ascii(raw: str) -> Case:
    board_state = BoardState()
    player_moves: list[PlayerMove] = []

    player_id = uuid.UUID("00000000-0000-0000-0000-000000000000")

    max_x = None
    y = -1
    for line in raw.splitlines():
        if not line or line.startswith("#"):
            continue
        y += 1
        x = -1
        for c in line:
            x += 1
            if max_x is None or x > max_x:
                max_x = x
            pos = Position(x=x, y=y)
            add_piece = False
            piece_id = uuid.uuid4()
            match c:
                case "x" | " ":
                    continue
                case "o":
                    add_piece = True
                case "^":
                    add_piece = True
                    player_moves.append(
                        PlayerMove(piece_id=piece_id, action=PieceAction.MOVE_UP)
                    )
                case "v":
                    add_piece = True
                    player_moves.append(
                        PlayerMove(piece_id=piece_id, action=PieceAction.MOVE_DOWN)
                    )
                case "<":
                    add_piece = True
                    player_moves.append(
                        PlayerMove(piece_id=piece_id, action=PieceAction.MOVE_LEFT)
                    )
                case ">":
                    add_piece = True
                    player_moves.append(
                        PlayerMove(piece_id=piece_id, action=PieceAction.MOVE_RIGHT)
                    )
                case "_":
                    raise NotImplementedError

            if add_piece:
                board_state._piece_by_position[pos] = PieceInformation(
                    player_id=player_id, piece_id=piece_id
                )

    width = 0 if max_x is None else max_x + 1
    return Case(
        width=width,
        height=y + 1,
        board_state=board_state,
        player_moves=player_moves,
    )


def static_board_state_to_ascii(
    board_state: BoardState, width: int, height: int
) -> str:
    lines = []
    for y in range(height):
        line = ""
        for x in range(width):
            piece = board_state.get_piece_at_position(Position(x=x, y=y))
            if piece is None:
                line += " "
            else:
                line += "o"
        lines.append(line)
    return "\n".join(lines)


def pytest_generate_tests(metafunc: pytest.Metafunc):
    if "board_state_path" not in metafunc.fixturenames:
        return
    metafunc.parametrize(
        "board_state_path", BOARD_STATES_DIR.glob("*.txt"), ids=lambda p: p.stem
    )


def test_board_state(board_state_path: Path):
    content = board_state_path.read_text("utf-8")
    before_state, _, expected_after_state = content.strip("\n").partition("\n---\n")
    test_case = case_from_ascii(before_state)
    # shuffle moves because we want the outcome to be independent
    random.shuffle(test_case.player_moves)
    test_case.board_state.perform_player_moves(test_case.player_moves)
    got_after_state = static_board_state_to_ascii(
        test_case.board_state, test_case.width, test_case.height
    )
    if got_after_state != expected_after_state:
        pytest.fail(
            f"expected state:\n{expected_after_state}\ngot state:\n{got_after_state}",
        )
