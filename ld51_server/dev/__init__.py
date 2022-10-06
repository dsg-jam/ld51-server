from fastapi import APIRouter, HTTPException, status

from ..protocol import Message, get_all_message_types

router = APIRouter(prefix="/dev-tools", tags=["dev-tools"])


@router.get("/protocol/schema")
def get_protocol_schema():
    return Message.schema()


@router.get(
    "/protocol/schema/{msg_type}",
    responses={status.HTTP_404_NOT_FOUND: {}},
)
def get_protocol_schema_for_msg(msg_type: str):
    for msg_cls in get_all_message_types():
        if msg_cls.get_type_value() == msg_type:
            return msg_cls.schema()
    raise HTTPException(status.HTTP_404_NOT_FOUND)
