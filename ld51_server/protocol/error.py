import uuid
from typing import Any, Literal

from pydantic import BaseModel, Field

from .base import BaseMessage


class ErrorPayload(BaseModel):
    type: str
    message: str | None
    extra: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def must_be_host(cls):
        return cls(
            type="protocol:forbidden",
            message="only the host may perform this operation",
        )

    @classmethod
    def invalid_lobby_state(cls):
        return cls(
            type="protocol:flow",
            message="the lobby isn't in the correct state for this message",
        )

    @classmethod
    def unhandled_message(cls):
        return cls(
            type="protocol:flow", message="this message isn't handled by the server"
        )

    @classmethod
    def illegal_player_move(cls, *, piece_id: uuid.UUID, message: str | None = None):
        return cls(
            type="game:illegal-move",
            message=message,
            extra={"piece_id": str(piece_id)},
        )


class ErrorMessage(BaseMessage[Literal["error"], ErrorPayload]):
    ...


__all__ = [
    ErrorPayload.__name__,
    ErrorMessage.__name__,
]
