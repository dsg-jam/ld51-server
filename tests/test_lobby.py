from typing import Type, TypeVar

import pytest
from fastapi.testclient import TestClient
from starlette.testclient import WebSocketTestSession

from ld51_server import app
from ld51_server.protocol import (
    Message,
    MessagePayloadT,
    PlayerJoinedPayload,
    ServerHelloPayload,
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
