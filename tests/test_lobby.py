import time
import uuid
from typing import Any, Type, TypeVar

import pytest
from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient
from starlette.testclient import WebSocketTestSession

from ld51_server import app
from ld51_server.models import (
    BoardPlatform,
    BoardPlatformTile,
    BoardPlatformTileType,
    Direction,
    GameOver,
    PieceAction,
    PlayerMove,
    Position,
    PushOutcome,
    PushOutcomePayload,
    TimelineEvent,
    TimelineEventAction,
)
from ld51_server.protocol import (
    BaseMessage,
    HostStartGameMessage,
    HostStartGamePayload,
    Message,
    MessagePayloadType,
    PlayerJoinedPayload,
    PlayerMovesMessage,
    PlayerMovesPayload,
    ReadyForNextRoundMessage,
    ReadyForNextRoundPayload,
    RoundResultPayload,
    RoundStartPayload,
    ServerHelloPayload,
    ServerStartGamePayload,
)


def _create_lobby(client: TestClient) -> str:
    resp = client.post("/lobby")
    return resp.json()["lobby_id"]


def _lobby_connect_ws(client: TestClient, lobby_id: str) -> WebSocketTestSession:
    ws: WebSocketTestSession = client.websocket_connect(f"/lobby/{lobby_id}/join")
    return ws


def _rx_msg_payload(
    ws: WebSocketTestSession, *, timeout: float = 0.2
) -> MessagePayloadType:
    raw = ws._send_queue.get(timeout=timeout)  # type: ignore
    if isinstance(raw, BaseException):
        raise raw
    ws._raise_on_close(raw)  # type: ignore
    msg = Message.parse_raw(raw["text"])
    return msg.payload


def _tx_msg(ws: WebSocketTestSession, msg: BaseMessage[Any, Any]) -> None:
    ws.send_json(jsonable_encoder(msg))


def _tx_msg_broadcast(
    msg: BaseMessage[Any, Any], *clients: WebSocketTestSession
) -> None:
    for ws in clients:
        _tx_msg(ws, msg)


_MT = TypeVar("_MT", bound=MessagePayloadType)


def _rx_msg_payload_type(ws: WebSocketTestSession, ty: Type[_MT]) -> _MT:
    payload = _rx_msg_payload(ws)
    assert isinstance(payload, ty)
    return payload


@pytest.mark.timeout(5)
def test_join_two_players():
    client = TestClient(app)
    lobby_id = _create_lobby(client)

    with _lobby_connect_ws(client, lobby_id) as ws1:
        # first the host should've received a hello msg
        data = _rx_msg_payload_type(ws1, ServerHelloPayload)
        assert data.is_host is True
        assert data.player.number == 1

        with _lobby_connect_ws(client, lobby_id) as ws2:
            # and the other player too
            data = _rx_msg_payload_type(ws2, ServerHelloPayload)
            other_player_id = data.player.id
            assert data.is_host is False

            # the host should receive a join message for the other player
            data = _rx_msg_payload_type(ws1, PlayerJoinedPayload)
            assert data.player.id == other_player_id
            assert data.player.number == 2


def _game_first_round(
    ws1: WebSocketTestSession, ws2: WebSocketTestSession, *, ws1_player_id: uuid.UUID
) -> None:
    ws1_data = _rx_msg_payload_type(ws1, RoundStartPayload)
    assert ws1_data.round_number == 1
    assert len(ws1_data.board_state) == 4
    ws2_data = _rx_msg_payload_type(ws2, RoundStartPayload)
    assert ws2_data == ws1_data

    ws1_piece_id = next(
        piece.piece_id
        for piece in ws1_data.board_state
        if piece.player_id == ws1_player_id
    )

    _tx_msg(
        ws1,
        PlayerMovesMessage.from_payload(
            PlayerMovesPayload(
                moves=[PlayerMove(piece_id=ws1_piece_id, action=PieceAction.MOVE_UP)]
            )
        ),
    )
    _tx_msg(ws2, PlayerMovesMessage.from_payload(PlayerMovesPayload(moves=[])))

    ws1_data = _rx_msg_payload_type(ws1, RoundResultPayload)
    assert ws1_data.timeline == [
        TimelineEvent(
            actions=[
                TimelineEventAction(
                    player_id=ws1_player_id,
                    piece_id=ws1_piece_id,
                    action=PieceAction.MOVE_UP,
                )
            ],
            outcomes=[
                PushOutcome.build(
                    PushOutcomePayload(
                        pusher_piece_id=ws1_piece_id,
                        victim_piece_ids=[],
                        direction=Direction.UP,
                    ),
                )
            ],
        )
    ]
    assert ws1_data.game_over is None
    ws2_data = _rx_msg_payload_type(ws2, RoundResultPayload)
    assert ws2_data == ws1_data

    _tx_msg_broadcast(
        ReadyForNextRoundMessage.from_payload(ReadyForNextRoundPayload()), ws1, ws2
    )


def _game_second_round(
    ws1: WebSocketTestSession,
    ws2: WebSocketTestSession,
    *,
    ws1_player_id: uuid.UUID,
    ws2_player_id: uuid.UUID,
) -> None:
    ws1_data = _rx_msg_payload_type(ws1, RoundStartPayload)
    assert ws1_data.round_number == 2
    assert len(ws1_data.board_state) == 3
    ws2_data = _rx_msg_payload_type(ws2, RoundStartPayload)
    assert ws2_data == ws1_data

    ws1_piece_id = next(
        piece.piece_id
        for piece in ws1_data.board_state
        if piece.player_id == ws1_player_id
    )

    _tx_msg(
        ws1,
        PlayerMovesMessage.from_payload(
            PlayerMovesPayload(
                moves=[PlayerMove(piece_id=ws1_piece_id, action=PieceAction.MOVE_DOWN)]
            )
        ),
    )
    _tx_msg(ws2, PlayerMovesMessage.from_payload(PlayerMovesPayload(moves=[])))

    ws1_data = _rx_msg_payload_type(ws1, RoundResultPayload)
    assert ws1_data.timeline == [
        TimelineEvent(
            actions=[
                TimelineEventAction(
                    player_id=ws1_player_id,
                    piece_id=ws1_piece_id,
                    action=PieceAction.MOVE_DOWN,
                )
            ],
            outcomes=[
                PushOutcome.build(
                    PushOutcomePayload(
                        pusher_piece_id=ws1_piece_id,
                        victim_piece_ids=[],
                        direction=Direction.DOWN,
                    ),
                )
            ],
        )
    ]
    assert ws1_data.game_over == GameOver(winner_player_id=ws2_player_id)
    ws2_data = _rx_msg_payload_type(ws2, RoundResultPayload)
    assert ws2_data == ws1_data

    _tx_msg_broadcast(
        ReadyForNextRoundMessage.from_payload(ReadyForNextRoundPayload()), ws1, ws2
    )


@pytest.mark.timeout(5)
def test_game():
    client = TestClient(app)
    lobby_id = _create_lobby(client)

    import ld51_server.game.lobby

    ld51_server.game.lobby.ROUND_DURATION = 0.0
    ld51_server.game.lobby.PRE_GAME_DURATION = 0.0

    with _lobby_connect_ws(client, lobby_id) as ws1:
        ws1_data = _rx_msg_payload_type(ws1, ServerHelloPayload)
        ws1_player_id = ws1_data.player.id
        assert ws1_data.is_host is True

        with _lobby_connect_ws(client, lobby_id) as ws2:
            ws2_data = _rx_msg_payload_type(ws2, ServerHelloPayload)
            ws2_player_id = ws2_data.player.id

            _rx_msg_payload_type(ws1, PlayerJoinedPayload)

            # our platform is just 4 tiles in a row (horizontal)
            platform = BoardPlatform(
                tiles=[
                    BoardPlatformTile(
                        position=Position(x=x, y=0),
                        texture_id="unknown",
                        tile_type=BoardPlatformTileType.FLOOR,
                    )
                    for x in range(4)
                ]
            )

            # play two games in the same lobby to make sure the state transitions hold up
            for _ in range(2):
                _tx_msg(
                    ws1,
                    HostStartGameMessage.from_payload(
                        HostStartGamePayload(platform=platform)
                    ),
                )

                ws1_data = _rx_msg_payload_type(ws1, ServerStartGamePayload)
                assert ws1_data.platform == platform
                ws2_data = _rx_msg_payload_type(ws2, ServerStartGamePayload)
                assert ws2_data == ws1_data

                _game_first_round(ws1, ws2, ws1_player_id=ws1_player_id)
                _game_second_round(
                    ws1, ws2, ws1_player_id=ws1_player_id, ws2_player_id=ws2_player_id
                )
                # there's a small race condition here
                time.sleep(0.1)
