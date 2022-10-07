from typing import Any, Type, TypeVar

import pytest
from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient
from starlette.testclient import WebSocketTestSession

from ld51_server import app
from ld51_server.models import BoardPlatform
from ld51_server.protocol import (
    BaseMessage,
    HostStartGameMessage,
    HostStartGamePayload,
    Message,
    MessagePayloadT,
    PlayerJoinedPayload,
    ServerHelloPayload,
    ServerStartGamePayload,
)


def _create_lobby(client: TestClient) -> str:
    resp = client.post("/lobby")
    return resp.json()["lobby_id"]


def _lobby_connect_ws(client: TestClient, lobby_id: str) -> WebSocketTestSession:
    ws: WebSocketTestSession = client.websocket_connect(f"/lobby/{lobby_id}/join")
    return ws


def _rx_msg_payload(ws: WebSocketTestSession) -> MessagePayloadT:
    raw = ws.receive_json()
    msg = Message.parse_obj(raw)
    return msg.payload


def _tx_msg(ws: WebSocketTestSession, msg: BaseMessage[Any, Any]) -> None:
    ws.send_json(jsonable_encoder(msg))


_MT = TypeVar("_MT", bound=MessagePayloadT)


def _rx_msg_payload_type(ws: WebSocketTestSession, ty: Type[_MT]) -> _MT:
    payload = _rx_msg_payload(ws)
    assert isinstance(payload, ty)
    return payload


@pytest.mark.timeout(5)
def test_join_single_player():
    client = TestClient(app)
    lobby_id = _create_lobby(client)

    with _lobby_connect_ws(client, lobby_id) as ws:
        data = _rx_msg_payload_type(ws, ServerHelloPayload)
        assert data.is_host is True


@pytest.mark.timeout(5)
def test_join_two_players():
    client = TestClient(app)
    lobby_id = _create_lobby(client)

    with _lobby_connect_ws(client, lobby_id) as ws1:
        # first the host should've received a hello msg
        data = _rx_msg_payload_type(ws1, ServerHelloPayload)
        assert data.is_host is True

        with _lobby_connect_ws(client, lobby_id) as ws2:
            # and the other player too
            data = _rx_msg_payload_type(ws2, ServerHelloPayload)
            other_player_id = data.player_id
            assert data.is_host is False

            # the host should receive a join message for the other player
            data = _rx_msg_payload_type(ws1, PlayerJoinedPayload)
            assert data.player_id == other_player_id


@pytest.mark.timeout(5)
def test_game_start():
    client = TestClient(app)
    lobby_id = _create_lobby(client)

    with _lobby_connect_ws(client, lobby_id) as ws1:
        data = _rx_msg_payload_type(ws1, ServerHelloPayload)
        assert data.is_host is True

        platform = BoardPlatform(tiles=[])
        _tx_msg(
            ws1,
            HostStartGameMessage.from_payload(HostStartGamePayload(platform=platform)),
        )

        data = _rx_msg_payload_type(ws1, ServerStartGamePayload)
        assert data.platform == platform

        # TODO: send moves
