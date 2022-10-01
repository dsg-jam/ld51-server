# Protocol

## Websocket Protocol

### Flow

- TODO: game start
- Start Round Loop

#### Round Loop

- Server: `round_start`
- Client x: `player_moves`
- Server: `round_result`
- Client x: `ready_for_next_round`
- restart loop

### Enums

#### Directions

- up
- down
- left
- right

#### Piece Actions

- no_action
- move_up
- move_down
- move_left
- move_right

### Messages

#### Server: Round Start Message

```json
{
    "type": "round_start",
    "payload": {
        "round_number": 2,
        "round_duration": 10,
        "board_state": [
            {
                "piece_id": "123e4567-e89b-12d3-a456-426614174000",
                "player_id": "123e4567-e89b-12d3-a456-426614174000",
                "position": {
                    "x": 0,
                    "y": 1
                }
            },
            {
                "piece_id": "123e4567-e89b-12d3-a456-426614174001",
                "player_id": "123e4567-e89b-12d3-a456-426614174000",
                "position": {
                    "x": 10,
                    "y": 15
                }
            }
        ]
    }
}
```

#### Server: Round Result Message

```json
{
    "type": "round_result",
    "payload": {
        "timeline": [
            {
                "actions": [
                    {
                        "player_id": "123e4567-e89b-12d3-a456-426614174000",
                        "piece_id": "123e4567-e89b-12d3-a456-426614174000",
                        "action": "piece action enum"
                    }
                ],
                "outcomes": [
                    {
                        "type": "outcome type",
                        "payload": {}
                    }
                ]
            }
        ],
        "game_over": {
            "winner_player_id": "123e4567-e89b-12d3-a456-426614174000"
        }
    }
}
```

##### Move

```json
{
    "type": "move",
    "payload": {
        "piece_id": "123e4567-e89b-12d3-a456-426614174000",
        "off_board": false,
        "new_position": {
            "x": 10,
            "y": 15
        }
    }
}
```

##### Move Conflict

```json
{
    "type": "move_conflict",
    "payload": {
        "piece_ids": [
            "123e4567-e89b-12d3-a456-426614174000",
        ],
        "collision_point": {
            "x": 10,
            "y": 15
        }
    }
}
```

##### Push

```json
{
    "type": "push",
    "payload": {
        "pusher_piece_id": "123e4567-e89b-12d3-a456-426614174000",
        "victim_piece_ids": [
            "123e4567-e89b-12d3-a456-426614174000"
        ],
        "direction": "direction enum"
    }
}
```

##### Push Conflict

```json
{
    "type": "push_conflict",
    "payload": {
        "piece_ids": [
            "123e4567-e89b-12d3-a456-426614174000"
        ],
        "collision_point": {
            "x": 10,
            "y": 15
        }
    }
}
```

#### Client: Player Move Message

```json
{
    "type": "player_moves",
    "payload": {
        "moves": [
            {
                "piece_id": "123e4567-e89b-12d3-a456-426614174000",
                "action": "piece action enum"
            },
            {
                "piece_id": "123e4567-e89b-12d3-a456-426614174001",
                "action": "piece action enum"
            }
        ]
    }
}
```

#### Client: Ready For Next Round Message

```json
{
    "type": "ready_for_next_round"
}
```
