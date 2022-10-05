from typing import Union

from pydantic import BaseModel, Field

from .game_loop import *
from .lobby import *

MessageT = Union[GameLoopMessageT, LobbyMessageT]
MessagePayloadT = Union[GameLoopMessagePayloadT, LobbyMessagePayloadT]


class Message(BaseModel):
    __root__: MessageT = Field(discriminator="type")

    @property
    def payload(self) -> MessagePayloadT:
        return self.__root__.payload
