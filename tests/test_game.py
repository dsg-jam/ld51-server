import random
from pathlib import Path

import pytest
from pydantic import BaseModel, ValidationError

from ld51_server.models import OutcomeType, TimelineEvent

from . import DATA_DIR
from .ascii_board import AsciiStateAndMoves

BOARD_STATES_DIR = DATA_DIR / "board_states"

TIMELINE_FILE_SUFFIX = ".timeline.json"
BOARD_STATE_FILE_SUFFIX = ".txt"


def pytest_generate_tests(metafunc: pytest.Metafunc):
    if "board_state_path" in metafunc.fixturenames:
        metafunc.parametrize(
            "board_state_path",
            BOARD_STATES_DIR.glob(f"*{BOARD_STATE_FILE_SUFFIX}"),
            ids=lambda p: p.stem,
        )
    if "timeline_path" in metafunc.fixturenames:
        metafunc.parametrize(
            "timeline_path",
            BOARD_STATES_DIR.glob(f"*{TIMELINE_FILE_SUFFIX}"),
            ids=lambda p: p.name[: -len(TIMELINE_FILE_SUFFIX)],
        )


def _load_before_after(
    board_state_path: Path,
) -> tuple[AsciiStateAndMoves, AsciiStateAndMoves]:
    raw_file_content = board_state_path.read_text("utf-8")
    raw_before_state, _, raw_after_state = raw_file_content.strip("\n").partition(
        "\n---\n"
    )
    before_state = AsciiStateAndMoves.parse(raw_before_state)
    after_state = AsciiStateAndMoves.parse(raw_after_state)
    return before_state, after_state


def test_board_state(board_state_path: Path):
    board_before, expected_board_after = _load_before_after(board_state_path)

    state_and_moves = board_before.to_board_state_and_moves()
    random.shuffle(state_and_moves.player_moves)
    state_and_moves.board_state.perform_player_moves(
        state_and_moves.get_validated_moves()
    )

    got_board_after = AsciiStateAndMoves.from_board_state(
        state_and_moves.board_state,
        width=expected_board_after.width,
        height=expected_board_after.height,
    )

    ascii_expected_after = expected_board_after.render()
    ascii_got_after = got_board_after.render()

    if ascii_expected_after != ascii_got_after:
        pytest.fail(
            f"got a different state than expected\nexpected state:\n{ascii_expected_after}\ngot state:\n{ascii_got_after}",
        )


class Timeline(BaseModel):
    __root__: list[TimelineEvent]


def _normalize_outcome(outcome: OutcomeType):
    payload = outcome.payload
    try:
        payload.piece_ids.sort()  # type: ignore
    except Exception:
        pass


def _normalize_events(events: list[TimelineEvent]) -> None:
    for event in events:
        event.actions.sort(key=lambda a: a.piece_id)
        for outcome in event.outcomes:
            _normalize_outcome(outcome)
        event.outcomes.sort(key=lambda e: e.json())


def test_timeline(timeline_path: Path):
    board_state_filename = (
        timeline_path.name[: -len(TIMELINE_FILE_SUFFIX)] + BOARD_STATE_FILE_SUFFIX
    )
    board_state_path = timeline_path.with_name(board_state_filename)
    board_before, _ = _load_before_after(board_state_path)

    state_and_moves = board_before.to_board_state_and_moves()
    random.shuffle(state_and_moves.player_moves)
    events = state_and_moves.board_state.perform_player_moves(
        state_and_moves.get_validated_moves()
    )
    _normalize_events(events)

    try:
        timeline = Timeline.parse_file(timeline_path)
        if timeline.__root__ == events:
            return
    except ValidationError:
        pass

    timeline_path.write_text(Timeline.parse_obj(events).json(indent=2))
    pytest.fail("updated expected")
