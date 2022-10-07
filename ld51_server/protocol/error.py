from typing import Literal

from pydantic import BaseModel, Field

from .base import BaseMessage


class ErrorPayload(BaseModel):
    type_: str = Field(alias="type")
    message: str | None


class ErrorMessage(BaseMessage[Literal["error"], ErrorPayload]):
    ...


__all__ = [
    ErrorPayload.__name__,
    ErrorMessage.__name__,
]
