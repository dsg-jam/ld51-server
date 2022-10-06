import uuid
from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field

from .general import Direction, PieceAction, Position


class MoveConflictOutcomePayload(BaseModel):
    piece_ids: list[uuid.UUID]
    collision_point: Position


class MoveConflictOutcome(BaseModel):
    type: Literal["move_conflict"]
    payload: MoveConflictOutcomePayload

    @classmethod
    def build(cls, payload: MoveConflictOutcomePayload):
        return cls(type="move_conflict", payload=payload)


class PushOutcomePayload(BaseModel):
    pusher_piece_id: uuid.UUID
    # TODO need to indicate if the piece is off the board
    victim_piece_ids: list[uuid.UUID]
    direction: Direction


class PushOutcome(BaseModel):
    type: Literal["push"]
    payload: PushOutcomePayload

    @classmethod
    def build(cls, payload: PushOutcomePayload):
        return cls(type="push", payload=payload)


class PushConflictOutcomePayload(BaseModel):
    piece_ids: list[uuid.UUID]
    collision_point: Position | None


class PushConflictOutcome(BaseModel):
    type: Literal["push_conflict"]
    payload: PushConflictOutcomePayload

    @classmethod
    def build(cls, payload: PushConflictOutcomePayload):
        return cls(type="push_conflict", payload=payload)


OutcomeT = Annotated[
    Union[MoveConflictOutcome, PushOutcome, PushConflictOutcome],
    Field(discriminator="type"),
]
OutcomePayloadT = Union[
    MoveConflictOutcomePayload,
    PushOutcomePayload,
    PushConflictOutcomePayload,
]


class TimelineEventAction(BaseModel):
    player_id: uuid.UUID
    piece_id: uuid.UUID
    action: PieceAction


class TimelineEvent(BaseModel):
    actions: list[TimelineEventAction]
    outcomes: list[OutcomeT]

    def is_empty(self) -> bool:
        return (not self.actions) and (not self.outcomes)


__all__ = [
    MoveConflictOutcomePayload.__name__,
    MoveConflictOutcome.__name__,
    PushOutcomePayload.__name__,
    PushOutcome.__name__,
    PushConflictOutcomePayload.__name__,
    PushConflictOutcome.__name__,
    "OutcomeT",
    "OutcomePayloadT",
    TimelineEventAction.__name__,
    TimelineEvent.__name__,
]
