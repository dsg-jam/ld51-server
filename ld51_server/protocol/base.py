import typing
from typing import Generic, TypeVar

from pydantic import BaseModel
from pydantic.generics import GenericModel

_TypeT = TypeVar("_TypeT")
_PayloadT = TypeVar("_PayloadT", bound=BaseModel)


class BaseMessage(GenericModel, Generic[_TypeT, _PayloadT]):
    type: _TypeT
    payload: _PayloadT

    @classmethod
    def get_type_value(cls) -> str:
        field = cls.__fields__["type"]
        (lit_value,) = typing.get_args(field.type_)
        return lit_value

    @classmethod
    def from_payload(cls, payload: _PayloadT):
        return cls(type=cls.get_type_value(), payload=payload)
