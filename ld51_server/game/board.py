import dataclasses
import uuid

from ..models import (
    Direction,
    MoveConflictOutcome,
    MoveConflictOutcomePayload,
    PlayerMove,
    PlayerPiecePosition,
    Position,
    PushConflictOutcome,
    PushConflictOutcomePayload,
    PushOutcome,
    PushOutcomePayload,
    TimelineEvent,
    TimelineEventAction,
)
from .board_platform import BoardPlatformABC, InfiniteBoardPlatform


@dataclasses.dataclass(kw_only=True)
class PieceInformation:
    player_id: uuid.UUID
    piece_id: uuid.UUID

    @classmethod
    def from_player_piece_position(cls, piece: PlayerPiecePosition):
        return cls(player_id=piece.player_id, piece_id=piece.piece_id)


@dataclasses.dataclass(kw_only=True)
class IllegalPlayerMoveError(Exception):
    piece_id: uuid.UUID
    message: str | None = None


class PlayerMovesExhaustedError(Exception):
    ...


class Board:
    _platform: BoardPlatformABC
    _piece_by_position: dict[Position, PieceInformation]

    def __init__(self) -> None:
        self._platform = InfiniteBoardPlatform()
        self._piece_by_position = {}

    def get_piece_by_id(self, piece_id: uuid.UUID) -> PlayerPiecePosition | None:
        for pos, info in self._piece_by_position.items():
            if info.piece_id == piece_id:
                return PlayerPiecePosition(**dataclasses.asdict(info), position=pos)
        return None

    def get_piece_at_position(self, pos: Position) -> PlayerPiecePosition | None:
        info = self._piece_by_position.get(pos)
        if info is None:
            return None
        return PlayerPiecePosition(**dataclasses.asdict(info), position=pos)

    def get_pieces_model(self) -> list[PlayerPiecePosition]:
        pieces: list[PlayerPiecePosition] = []
        for pos, info in self._piece_by_position.items():
            piece = PlayerPiecePosition(**dataclasses.asdict(info), position=pos)
            pieces.append(piece)
        return pieces

    def _execute_push_outcomes(self, pushes: list[PushOutcomePayload]) -> None:
        if not pushes:
            return

        temp_piece_by_positions: dict[Position, PieceInformation] = {}
        for push_outcome in pushes:
            piece_ids = (push_outcome.pusher_piece_id, *push_outcome.victim_piece_ids)
            for piece_id in piece_ids:
                info = self.get_piece_by_id(piece_id)
                assert info is not None
                old_pos = info.position
                new_pos = old_pos.offset_in_direction(push_outcome.direction)
                assert new_pos not in temp_piece_by_positions
                piece = self._piece_by_position.pop(old_pos)
                if self._platform.is_position_on_board(new_pos):
                    # only keep the piece around if the new pos is still on the board
                    temp_piece_by_positions[new_pos] = piece

        for new_pos in temp_piece_by_positions:
            assert new_pos not in self._piece_by_position
        self._piece_by_position.update(temp_piece_by_positions)

    def _isolate_complete_push_chains(
        self,
        remaining_moves_by_piece_id: dict[uuid.UUID, Direction],
        complete_push_chains: dict[uuid.UUID, list[uuid.UUID]],
    ) -> int:
        incomple_push_chains: dict[uuid.UUID, list[uuid.UUID]] = {}

        victim_chain_length = -1
        while remaining_moves_by_piece_id:
            victim_chain_length += 1
            finished = False
            for pusher_piece_id, push_dir in remaining_moves_by_piece_id.copy().items():
                pusher_piece = self.get_piece_by_id(pusher_piece_id)
                if pusher_piece is None:
                    # this piece no longer exists
                    del remaining_moves_by_piece_id[pusher_piece_id]
                    continue
                try:
                    push_chain = incomple_push_chains[pusher_piece_id]
                except KeyError:
                    push_chain = incomple_push_chains[pusher_piece_id] = [
                        pusher_piece_id
                    ]
                victim_pos = pusher_piece.position.offset_in_direction(
                    push_dir, steps=victim_chain_length + 1
                )
                victim_piece = self.get_piece_at_position(victim_pos)
                if victim_piece is not None:
                    push_chain.append(victim_piece.piece_id)
                    continue

                complete_push_chains[pusher_piece_id] = push_chain
                finished = True

            if finished:
                break
        return victim_chain_length

    def _find_push_conflicts(
        self,
        complete_push_chains: dict[uuid.UUID, list[uuid.UUID]],
        remaining_moves_by_piece_id: dict[uuid.UUID, Direction],
        victim_chain_length: int,
    ) -> list[PushConflictOutcomePayload]:
        if victim_chain_length == 0:
            return []

        global_min_distance: int | None = None

        def update_global_min_distance(other: int) -> None:
            nonlocal global_min_distance
            if global_min_distance is None or other < global_min_distance:
                global_min_distance = other

        head_on_collisions: dict[frozenset[uuid.UUID], int] = {}
        victim_to_pushers: dict[uuid.UUID, tuple[int, list[uuid.UUID]]] = {}
        for push_chain in complete_push_chains.values():
            pusher_piece_id, *victim_piece_ids = push_chain
            for chain_idx, piece_id in enumerate(victim_piece_ids, 1):
                if piece_id in complete_push_chains:
                    del push_chain[chain_idx:]
                    collision_key = frozenset((pusher_piece_id, piece_id))
                    if collision_key in head_on_collisions:
                        # head-on collision already handled
                        break
                    pusher_a_dir = remaining_moves_by_piece_id[pusher_piece_id]
                    pusher_b_dir = remaining_moves_by_piece_id[piece_id]
                    if pusher_a_dir != pusher_b_dir.get_opposite():
                        # not a head-on collision
                        break
                    min_distance = victim_chain_length // 2
                    head_on_collisions[collision_key] = min_distance
                    update_global_min_distance(min_distance)
                    break

                try:
                    min_distance, pushers = victim_to_pushers[piece_id]
                except KeyError:
                    min_distance = None
                    pushers = []  # will be overwritten anyway

                if min_distance is None or chain_idx < min_distance:
                    min_distance = chain_idx
                    pushers = [pusher_piece_id]
                elif chain_idx == min_distance:
                    pushers.append(pusher_piece_id)

                victim_to_pushers[piece_id] = (min_distance, pushers)
                if len(pushers) >= 2:
                    update_global_min_distance(min_distance)

        outcomes: list[PushConflictOutcomePayload] = []
        if global_min_distance is None:
            return outcomes

        for (
            pusher_a_piece_id,
            pusher_b_piece_id,
        ), distance in head_on_collisions.items():
            if distance != global_min_distance:
                continue
            outcomes.append(
                PushConflictOutcomePayload(
                    piece_ids=[pusher_a_piece_id, pusher_b_piece_id],
                    # TODO: determine
                    collision_point=None,
                )
            )
        if outcomes:
            # we have head-on collisions that need to be handled first
            return outcomes

        for distance, pushers in victim_to_pushers.values():
            if distance != global_min_distance:
                continue
            if len(pushers) < 2:
                continue
            outcomes.append(
                PushConflictOutcomePayload(
                    piece_ids=pushers,
                    # TODO: determine
                    collision_point=None,
                )
            )

        return outcomes

    def _perform_player_move_event(
        self,
        action_by_piece_id: dict[uuid.UUID, TimelineEventAction],
        remaining_moves_by_piece_id: dict[uuid.UUID, Direction],
    ) -> TimelineEvent:
        event = TimelineEvent(actions=[], outcomes=[])
        complete_push_chains: dict[uuid.UUID, list[uuid.UUID]] = {}
        victim_chain_length = self._isolate_complete_push_chains(
            remaining_moves_by_piece_id, complete_push_chains
        )

        if not complete_push_chains:
            raise PlayerMovesExhaustedError()

        if collision_outcomes := self._find_push_conflicts(
            complete_push_chains, remaining_moves_by_piece_id, victim_chain_length
        ):
            for outcome in collision_outcomes:
                for piece_id in outcome.piece_ids:
                    event.actions.append(action_by_piece_id[piece_id])
                    del remaining_moves_by_piece_id[piece_id]
                event.outcomes.append(PushConflictOutcome.build(outcome))
            return event

        target_pos_to_pushers: dict[Position, list[uuid.UUID]] = {}
        for pusher_piece_id, push_chain in complete_push_chains.items():
            pusher_piece = self.get_piece_by_id(pusher_piece_id)
            assert pusher_piece is not None
            push_dir = remaining_moves_by_piece_id[pusher_piece_id]
            target_pos = pusher_piece.position.offset_in_direction(
                push_dir, steps=len(push_chain)
            )
            try:
                target_pos_to_pushers[target_pos].append(pusher_piece_id)
            except KeyError:
                target_pos_to_pushers[target_pos] = [pusher_piece_id]

        for target_pos, pushers in target_pos_to_pushers.items():
            if len(pushers) < 2:
                continue

            # multiple pieces trying to occupy the same empty spot
            for piece_id in pushers:
                del remaining_moves_by_piece_id[piece_id]
                del complete_push_chains[piece_id]
            event.actions.extend(action_by_piece_id[piece_id] for piece_id in pushers)
            event.outcomes.append(
                MoveConflictOutcome.build(
                    MoveConflictOutcomePayload(
                        piece_ids=pushers,
                        collision_point=target_pos,
                    )
                )
            )

        push_outcomes: list[PushOutcomePayload] = []
        for push_chain in complete_push_chains.values():
            pusher_piece_id, *victim_piece_ids = push_chain
            event.actions.append(action_by_piece_id[pusher_piece_id])
            push_outcome = PushOutcomePayload(
                pusher_piece_id=pusher_piece_id,
                victim_piece_ids=victim_piece_ids,
                direction=remaining_moves_by_piece_id[pusher_piece_id],
            )
            push_outcomes.append(push_outcome)
            event.outcomes.append(PushOutcome.build(push_outcome))
            del remaining_moves_by_piece_id[pusher_piece_id]

        self._execute_push_outcomes(push_outcomes)

        return event

    def verify_player_moves(
        self, player_id: uuid.UUID, planned_moves: list[PlayerMove]
    ) -> list[TimelineEventAction]:
        event_actions: list[TimelineEventAction] = []
        for move in planned_moves:
            piece = self.get_piece_by_id(move.piece_id)
            if piece is None:
                raise IllegalPlayerMoveError(
                    piece_id=move.piece_id, message="piece not found"
                )

            if piece.player_id != player_id:
                raise IllegalPlayerMoveError(
                    piece_id=move.piece_id, message="piece not owned by this player"
                )

            event_actions.append(
                TimelineEventAction(
                    player_id=piece.player_id,
                    piece_id=move.piece_id,
                    action=move.action,
                )
            )

        return event_actions

    def perform_player_moves(self, moves: list[PlayerMove]) -> list[TimelineEvent]:
        # TODO: verify player moves:
        #   - piece must exist and be owned by the player

        action_by_piece_id: dict[uuid.UUID, TimelineEventAction] = {}
        for move in moves:
            # TODO: switch to moves: TimelineEventAction and use a separate validation function to convert playermove to it
            piece = self.get_piece_by_id(move.piece_id)
            assert piece is not None
            action_by_piece_id[move.piece_id] = TimelineEventAction(
                player_id=piece.player_id, piece_id=move.piece_id, action=move.action
            )

        remaining_moves_by_piece_id: dict[uuid.UUID, Direction] = {}
        # populate remaining moves
        for move in moves:
            move_dir = move.action.as_direction()
            if move_dir is None:
                continue
            remaining_moves_by_piece_id[move.piece_id] = move_dir

        events: list[TimelineEvent] = []
        while remaining_moves_by_piece_id:
            try:
                event = self._perform_player_move_event(
                    action_by_piece_id, remaining_moves_by_piece_id
                )
            except PlayerMovesExhaustedError:
                break
            events.append(event)

        return events
