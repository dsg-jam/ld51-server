from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field

from .general import GameOver, PlayerMove, PlayerPiecePosition
from .timeline import TimelineEvent


class RoundStartPayload(BaseModel):
    round_number: int
    round_duration: float
    board_state: list[PlayerPiecePosition]


class RoundStartMessage(BaseModel):
    type: Literal["round_start"]
    payload: RoundStartPayload


class RoundResultPayload(BaseModel):
    timeline: list[TimelineEvent]
    game_over: GameOver | None


class RoundResultMessage(BaseModel):
    type: Literal["round_result"]
    payload: RoundResultPayload


class PlayerMovesPayload(BaseModel):
    moves: list[PlayerMove]


class PlayerMovesMessage(BaseModel):
    type: Literal["player_moves"]
    payload: PlayerMovesPayload


class ReadyForNextRoundPayload(BaseModel):
    ...


class ReadyForNextRoundMessage(BaseModel):
    type: Literal["ready_for_next_round"]
    payload: ReadyForNextRoundPayload = Field(default_factory=ReadyForNextRoundPayload)


MessageT = Union[
    RoundStartMessage,
    RoundResultMessage,
    PlayerMovesMessage,
    ReadyForNextRoundMessage,
]
MessagePayloadT = Union[
    RoundStartPayload,
    RoundResultPayload,
    PlayerMovesPayload,
    ReadyForNextRoundPayload,
]


class Message(BaseModel):
    __root__: Annotated[
        MessageT,
        Field(discriminator="type"),
    ]

    @property
    def payload(self) -> MessagePayloadT:
        return self.__root__.payload


__all__ = [
    RoundStartPayload.__name__,
    RoundStartMessage.__name__,
    RoundResultPayload.__name__,
    RoundResultMessage.__name__,
    PlayerMovesPayload.__name__,
    PlayerMovesMessage.__name__,
    ReadyForNextRoundPayload.__name__,
    ReadyForNextRoundMessage.__name__,
    Message.__name__,
]
