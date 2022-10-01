from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field

from .general import GameOver, PlayerMove, PlayerPiecePosition
from .timeline import TimelineEvent


class RoundStartMessagePayload(BaseModel):
    round_number: int
    round_duration: float
    board_state: list[PlayerPiecePosition]


class RoundStartMessage(BaseModel):
    type: Literal["round_start"]
    payload: RoundStartMessagePayload


class RoundResultMessagePayload(BaseModel):
    timeline: list[TimelineEvent]
    game_over: GameOver | None


class RoundResultMessage(BaseModel):
    type: Literal["round_result"]
    payload: RoundResultMessagePayload


class PlayerMovesMessagePayload(BaseModel):
    moves: list[PlayerMove]


class PlayerMovesMessage(BaseModel):
    type: Literal["player_moves"]
    payload: PlayerMovesMessagePayload


class ReadyForNextRoundMessage(BaseModel):
    type: Literal["ready_for_next_round"]


class Message(BaseModel):
    __root__: Annotated[
        Union[
            RoundStartMessage,
            RoundResultMessage,
            PlayerMovesMessage,
            ReadyForNextRoundMessage,
        ],
        Field(discriminator="type"),
    ]


__all__ = [
    RoundStartMessagePayload.__name__,
    RoundStartMessage.__name__,
    RoundResultMessagePayload.__name__,
    RoundResultMessage.__name__,
    PlayerMovesMessagePayload.__name__,
    PlayerMovesMessage.__name__,
    ReadyForNextRoundMessage.__name__,
    Message.__name__,
]
