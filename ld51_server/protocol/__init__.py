import typing
from typing import Any, Type, Union

from pydantic import BaseModel, Field

from .base import BaseMessage
from .error import *
from .game_loop import *
from .lobby import *

MessageType = Union[ErrorMessage, GameLoopMessageType, LobbyMessageType]
MessagePayloadType = Union[
    ErrorPayload, GameLoopMessagePayloadType, LobbyMessagePayloadType
]


class Message(BaseModel):
    __root__: MessageType = Field(discriminator="type")

    @property
    def payload(self) -> MessagePayloadType:
        return self.__root__.payload


def get_all_message_types() -> tuple[Type[BaseMessage[Any, Any]]]:
    return typing.get_args(MessageType)
