import uuid
from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field

from .general import Direction, PieceAction, Position


class MoveOutcomePayload(BaseModel):
    piece_id: uuid.UUID
    off_board: bool
    new_position: Position


class MoveOutcome(BaseModel):
    type: Literal["move"]
    payload: MoveOutcomePayload


class MoveConflictOutcomePayload(BaseModel):
    piece_ids: list[uuid.UUID]
    collision_point: Position


class MoveConflictOutcome(BaseModel):
    type: Literal["move_conflict"]
    payload: MoveConflictOutcomePayload


class PushOutcomePayload(BaseModel):
    pusher_piece_id: uuid.UUID
    # TODO need to indicate if the piece is off the board
    victim_piece_ids: list[uuid.UUID]
    direction: Direction


class PushOutcome(BaseModel):
    type: Literal["push"]
    payload: PushOutcomePayload


class PushConflictOutcomePayload(BaseModel):
    piece_ids: list[uuid.UUID]
    collision_point: Position


class PushConflictOutcome(BaseModel):
    type: Literal["push_conflict"]
    payload: PushConflictOutcomePayload


OutcomeT = Union[MoveOutcome, MoveConflictOutcome, PushOutcome, PushConflictOutcome]
OutcomePayloadT = Union[
    MoveOutcomePayload,
    MoveConflictOutcomePayload,
    PushOutcomePayload,
    PushConflictOutcomePayload,
]


class Outcome(BaseModel):
    __root__: Annotated[
        OutcomeT,
        Field(discriminator="type"),
    ]

    @property
    def payload(self) -> OutcomePayloadT:
        return self.__root__.payload


class TimelineEventAction(BaseModel):
    player_id: uuid.UUID
    piece_id: uuid.UUID
    action: PieceAction


class TimelineEvent(BaseModel):
    actions: list[TimelineEventAction]
    outcomes: list[Outcome]


__all__ = [
    MoveOutcomePayload.__name__,
    MoveOutcome.__name__,
    MoveConflictOutcomePayload.__name__,
    MoveConflictOutcome.__name__,
    PushOutcomePayload.__name__,
    PushOutcome.__name__,
    PushConflictOutcomePayload.__name__,
    PushConflictOutcome.__name__,
    "OutcomeT",
    "OutcomePayloadT",
    Outcome.__name__,
    TimelineEventAction.__name__,
    TimelineEvent.__name__,
]
