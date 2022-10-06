import typing
from typing import Generic, TypeVar

from pydantic import BaseModel
from pydantic.generics import GenericModel

_TYPE_T = TypeVar("_TYPE_T")
_PAYLOAD_T = TypeVar("_PAYLOAD_T", bound=BaseModel)


class BaseMessage(GenericModel, Generic[_TYPE_T, _PAYLOAD_T]):
    type: _TYPE_T
    payload: _PAYLOAD_T

    @classmethod
    def get_type_value(cls) -> str:
        field = cls.__fields__["type"]
        (lit_value,) = typing.get_args(field.type_)
        return lit_value

    @classmethod
    def from_payload(cls, payload: _PAYLOAD_T):
        return cls(type=cls.get_type_value(), payload=payload)
