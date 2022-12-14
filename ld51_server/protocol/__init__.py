import typing
from typing import Any, Type, Union

from pydantic import BaseModel, Field

from .base import BaseMessage
from .error import *
from .game_loop import *
from .lobby import *

MessageT = Union[ErrorMessage, GameLoopMessageT, LobbyMessageT]
MessagePayloadT = Union[ErrorPayload, GameLoopMessagePayloadT, LobbyMessagePayloadT]


class Message(BaseModel):
    __root__: MessageT = Field(discriminator="type")

    @property
    def payload(self) -> MessagePayloadT:
        return self.__root__.payload


def get_all_message_types() -> tuple[Type[BaseMessage[Any, Any]]]:
    return typing.get_args(MessageT)
