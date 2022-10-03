import dataclasses
import uuid

import networkx

from .models import (
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
)


class IllegalMoveException(Exception):
    ...


@dataclasses.dataclass()
class PlayerMoveByPlayer:
    player_id: uuid.UUID
    move: PlayerMove


@dataclasses.dataclass()
class PieceInformation:
    player_id: uuid.UUID
    piece_id: uuid.UUID

    @classmethod
    def from_player_piece_position(cls, piece: PlayerPiecePosition):
        return cls(player_id=piece.player_id, piece_id=piece.piece_id)


class BoardState:
    _piece_by_position: dict[Position, PieceInformation]

    def __init__(self) -> None:
        self._piece_by_position = {}

    def get_piece_by_id(self, piece_id: uuid.UUID) -> PlayerPiecePosition | None:
        for pos, info in self._piece_by_position.items():
            if info.piece_id == piece_id:
                return PlayerPiecePosition(**dataclasses.asdict(info), position=pos)
        return None

    def has_piece_at_position(self, pos: Position) -> bool:
        return pos in self._piece_by_position

    def get_piece_at_position(self, pos: Position) -> PlayerPiecePosition | None:
        info = self._piece_by_position.get(pos)
        if info is None:
            return None
        return PlayerPiecePosition(**dataclasses.asdict(info), position=pos)

    def set_piece_position(self, piece_id: uuid.UUID, new_pos: Position) -> None:
        assert new_pos not in self._piece_by_position
        info = self.get_piece_by_id(piece_id)

        del self._piece_by_position[info.position]
        self._piece_by_position[new_pos] = PieceInformation.from_player_piece_position(
            info
        )

    def _execute_push_chains(self, pushes: list[PushOutcomePayload]) -> None:
        if not pushes:
            return

        temp_piece_by_positions = {}
        for push_outcome in pushes:
            piece_ids = (push_outcome.pusher_piece_id, *push_outcome.victim_piece_ids)
            for piece_id in piece_ids:
                info = self.get_piece_by_id(piece_id)
                assert info is not None
                old_pos = info.position
                new_pos = old_pos.offset_in_direction(push_outcome.direction)
                assert new_pos not in temp_piece_by_positions
                temp_piece_by_positions[new_pos] = self._piece_by_position.pop(old_pos)
        for new_pos in temp_piece_by_positions.keys():
            assert new_pos not in self._piece_by_position
        self._piece_by_position.update(temp_piece_by_positions)

    def is_position_on_board(self, pos: Position) -> bool:
        #  TODO
        return True

    def _isolate_complete_push_chains(
        self,
        remaining_moves_by_piece_id: dict[uuid.UUID, Direction],
        complete_push_chains: dict[uuid.UUID, list[uuid.UUID]],
    ) -> None:
        chain_length = 0
        incomple_push_chains: dict[uuid.UUID, list[uuid.UUID]] = {}

        while remaining_moves_by_piece_id:
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
                    push_dir, steps=chain_length + 1
                )
                victim_piece = self.get_piece_at_position(victim_pos)
                if victim_piece is not None:
                    push_chain.append(victim_piece.piece_id)
                    continue

                complete_push_chains[pusher_piece_id] = push_chain
                finished = True

            if finished:
                return
            chain_length += 1

    def _remove_cycles(
        self, complete_push_chains: dict[uuid.UUID, list[uuid.UUID]]
    ) -> None:
        graph = networkx.DiGraph()
        for push_chain in complete_push_chains.values():
            pusher_a_piece_id, *victim_piece_ids = push_chain
            for pusher_b_piece_id in victim_piece_ids:
                if pusher_b_piece_id not in complete_push_chains:
                    # this isn't a pusher
                    continue
                graph.add_edge(pusher_a_piece_id, pusher_b_piece_id)

        for cycle_pieces in networkx.simple_cycles(graph):
            if len(cycle_pieces) <= 2:
                continue

            pusher_a_piece_id = cycle_pieces[-1]
            for pusher_b_piece_id in cycle_pieces:
                push_chain = complete_push_chains[pusher_a_piece_id]
                b_in_chain_index = push_chain.index(pusher_b_piece_id)
                del push_chain[b_in_chain_index:]
                pusher_a_piece_id = pusher_b_piece_id

    def _perform_player_move_event(
        self,
        moves_by_piece_id: dict[uuid.UUID, PlayerMove],
        remaining_moves_by_piece_id: dict[uuid.UUID, Direction],
    ) -> TimelineEvent:
        event = TimelineEvent(actions=[], outcomes=[])
        complete_push_chains: dict[uuid.UUID, list[uuid.UUID]] = {}
        self._isolate_complete_push_chains(
            remaining_moves_by_piece_id, complete_push_chains
        )
        self._remove_cycles(complete_push_chains)

        target_pos_to_pushers: dict[Position, list[uuid.UUID]] = {}
        victim_to_pushers: dict[uuid.UUID, list[uuid.UUID]] = {}
        for pusher_piece_id, push_chain in complete_push_chains.items():
            pusher_piece = self.get_piece_by_id(pusher_piece_id)
            push_dir = remaining_moves_by_piece_id[pusher_piece_id]
            target_pos = pusher_piece.position.offset_in_direction(
                push_dir, steps=len(push_chain)
            )
            try:
                target_pos_to_pushers[target_pos].append(pusher_piece_id)
            except KeyError:
                target_pos_to_pushers[target_pos] = [pusher_piece_id]

            for piece_id in push_chain:
                try:
                    victim_to_pushers[piece_id].append(pusher_piece_id)
                except KeyError:
                    victim_to_pushers[piece_id] = [pusher_piece_id]

        for target_pos, pushers in target_pos_to_pushers.items():
            if len(pushers) < 2:
                continue

            # multiple pieces trying to occupy the same empty spot
            for piece_id in pushers:
                del remaining_moves_by_piece_id[piece_id]
                del complete_push_chains[piece_id]
            event.actions.extend(moves_by_piece_id[piece_id] for piece_id in pushers)
            event.outcomes.append(
                MoveConflictOutcome.build(
                    MoveConflictOutcomePayload(
                        piece_ids=pushers,
                        collision_point=target_pos,
                    )
                )
            )

        handled_push_collisions: set[uuid.UUID] = set()
        for pushers in victim_to_pushers.values():
            if len(pushers) < 2:
                continue

            unhandled_collisions: set[uuid.UUID] = (
                set(pushers) - handled_push_collisions
            )
            if not unhandled_collisions:
                continue

            handled_push_collisions.update(unhandled_collisions)

            # multiple pieces are trying to push the same piece

            for piece_id in pushers:
                del remaining_moves_by_piece_id[piece_id]
                del complete_push_chains[piece_id]
            event.actions.extend(moves_by_piece_id[piece_id] for piece_id in pushers)
            event.outcomes.append(
                PushConflictOutcome.build(
                    PushConflictOutcomePayload(
                        piece_ids=pushers,
                        collision_point=target_pos,
                    )
                )
            )

        push_outcomes = []
        for push_chain in complete_push_chains.values():
            pusher_piece_id, *victim_piece_ids = push_chain
            event.actions.append(moves_by_piece_id[pusher_piece_id])
            push_outcome = PushOutcomePayload(
                pusher_piece_id=pusher_piece_id,
                victim_piece_ids=victim_piece_ids,
                direction=remaining_moves_by_piece_id[pusher_piece_id],
            )
            push_outcomes.append(push_outcome)
            event.outcomes.append(PushOutcome.build(push_outcome))
            del remaining_moves_by_piece_id[pusher_piece_id]

        self._execute_push_chains(push_outcomes)

        return event

    def perform_player_moves(self, moves: list[PlayerMove]) -> list[TimelineEvent]:
        # TODO: verify player moves:
        #   - piece must exist and be owned by the player

        moves_by_piece_id = {move.piece_id: move for move in moves}

        remaining_moves_by_piece_id: dict[uuid.UUID, Direction] = {}
        # populate remaining moves
        for move in moves:
            move_dir = move.action.as_direction()
            if move_dir is None:
                continue
            remaining_moves_by_piece_id[move.piece_id] = move_dir

        events = []
        while remaining_moves_by_piece_id:
            event = self._perform_player_move_event(
                moves_by_piece_id, remaining_moves_by_piece_id
            )
            events.append(event)
        return events
