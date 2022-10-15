from typing import Any, ClassVar

from fastapi import APIRouter, HTTPException, status

from ..protocol import Message, get_all_message_types
from .schema_value_generator import SchemaValueGenerator

router = APIRouter(prefix="/protocol")


@router.get("/schema", response_model=dict[str, Any])
def get_protocol_schema():
    return Message.schema()


class _MsgType(str):
    __cached_message_type_ids: ClassVar[list[str] | None] = None

    @classmethod
    def all_message_type_ids(cls) -> list[str]:
        if cls.__cached_message_type_ids is None:
            cls.__cached_message_type_ids = [
                msg_cls.get_type_value() for msg_cls in get_all_message_types()
            ]
        return cls.__cached_message_type_ids

    @classmethod
    def __modify_schema__(cls, field_schema: dict[str, Any]) -> None:
        field_schema.clear()
        field_schema.update({"enum": cls.all_message_type_ids()})


@router.get("/msg-types", response_model=list[str])
def list_message_types():
    return _MsgType.all_message_type_ids()


@router.get(
    "/schema/{msg_type}",
    response_model=dict[str, Any],
    responses={status.HTTP_404_NOT_FOUND: {}},
)
def get_schema_for_msg(msg_type: _MsgType) -> dict[str, Any]:
    for msg_cls in get_all_message_types():
        if msg_cls.get_type_value() == msg_type:
            return msg_cls.schema()
    raise HTTPException(status.HTTP_404_NOT_FOUND)


@router.get(
    "/example/{msg_type}",
    response_model=dict[str, Any],
    responses={status.HTTP_404_NOT_FOUND: {}},
)
def get_example_for_message(msg_type: _MsgType, seed: int | None = None):
    """Generate a random message for the given message type.

    The generated message fulfills the structural requirements of the message type, but is not necessarily semantically valid.
    """
    schema = get_schema_for_msg(msg_type)
    gen = SchemaValueGenerator(schema, seed=seed)
    return gen.generate()
