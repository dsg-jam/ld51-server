from typing import TypedDict


class Code(TypedDict):
    code: int
    reason: str | None


def _make(code: int, reason: str | None) -> Code:
    return {"code": code, "reason": reason}


# join errors
LOBBY_NOT_JOINABLE = _make(4001, "lobby not joinable")
LOBBY_NOT_FOUND = _make(4002, "lobby not found")
LOBBY_SESSION_EXPIRED = _make(4003, "session expired")

# lobby state errors
LOBBY_SHUTDOWN = _make(4101, "lobby shutting down")
INVALID_MESSAGE = _make(4102, "invalid message")
NO_MOVES_SUBMITTED = _make(4103, "no moves submitted")
