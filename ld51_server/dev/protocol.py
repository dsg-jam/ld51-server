from typing import Any

from fastapi import APIRouter, HTTPException, status

from ..protocol import Message, get_all_message_types
from .schema_value_generator import SchemaValueGenerator

router = APIRouter(prefix="/protocol")


@router.get("/schema")
def get_protocol_schema():
    return Message.schema()


@router.get("/msg-types")
def list_message_types():
    return [msg_cls.get_type_value() for msg_cls in get_all_message_types()]


@router.get(
    "/schema/{msg_type}",
    responses={status.HTTP_404_NOT_FOUND: {}},
)
def get_schema_for_msg(msg_type: str) -> dict[str, Any]:
    for msg_cls in get_all_message_types():
        if msg_cls.get_type_value() == msg_type:
            return msg_cls.schema()
    raise HTTPException(status.HTTP_404_NOT_FOUND)


@router.get(
    "/example/{msg_type}",
    responses={status.HTTP_404_NOT_FOUND: {}},
)
def get_example_for_message(msg_type: str, seed: int | None = None):
    """Generate a random message for the given message type.

    The generated message fulfills the structural requirements of the message type, but is not necessarily semantically valid.
    """
    schema = get_schema_for_msg(msg_type)
    gen = SchemaValueGenerator(schema, seed=seed)
    return gen.generate()
