from typing import Literal, Union

from pydantic import BaseModel

from ..models import GameOver, PlayerMove, PlayerPiecePosition, TimelineEvent
from .base import BaseMessage


class RoundStartPayload(BaseModel):
    round_number: int
    round_duration: float
    board_state: list[PlayerPiecePosition]


class RoundStartMessage(BaseMessage[Literal["round_start"], RoundStartPayload]):
    ...


class RoundResultPayload(BaseModel):
    timeline: list[TimelineEvent]
    game_over: GameOver | None


class RoundResultMessage(BaseMessage[Literal["round_result"], RoundResultPayload]):
    ...


class PlayerMovesPayload(BaseModel):
    moves: list[PlayerMove]


class PlayerMovesMessage(BaseMessage[Literal["player_moves"], PlayerMovesPayload]):
    ...


class ReadyForNextRoundPayload(BaseModel):
    ...


class ReadyForNextRoundMessage(
    BaseMessage[Literal["ready_for_next_round"], ReadyForNextRoundPayload]
):
    ...


GameLoopMessageT = Union[
    PlayerMovesMessage,
    ReadyForNextRoundMessage,
    RoundResultMessage,
    RoundStartMessage,
]
GameLoopMessagePayloadT = Union[
    PlayerMovesPayload,
    ReadyForNextRoundPayload,
    RoundResultPayload,
    RoundStartPayload,
]


__all__ = [
    "RoundStartPayload",
    "RoundStartMessage",
    "RoundResultPayload",
    "RoundResultMessage",
    "PlayerMovesPayload",
    "PlayerMovesMessage",
    "ReadyForNextRoundPayload",
    "ReadyForNextRoundMessage",
    "GameLoopMessageT",
    "GameLoopMessagePayloadT",
]
