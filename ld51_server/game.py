import dataclasses
import uuid
from typing import Iterator

from .models import (
    Direction,
    MoveConflictOutcome,
    MoveConflictOutcomePayload,
    MoveOutcome,
    MoveOutcomePayload,
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
                temp_piece_by_positions[new_pos] = self._piece_by_position.pop(old_pos)
        for new_pos in temp_piece_by_positions.keys():
            assert new_pos not in self._piece_by_position
        self._piece_by_position.update(temp_piece_by_positions)

    def is_position_on_board(self, pos: Position) -> bool:
        #  TODO
        return True

    def _phase1_moves(
        self,
        moves_by_piece_id: dict[uuid.UUID, PlayerMove],
        remaining_moves_by_piece_id: dict[uuid.UUID, Direction],
    ) -> Iterator[TimelineEvent]:
        while remaining_moves_by_piece_id:
            event = TimelineEvent(actions=[], outcomes=[])

            # map target position to pieces that want to move to that spot
            trivial_move_candidates: dict[Position, list[uuid.UUID]] = {}
            # map position to piece id and push direction
            collision_candidates: dict[Position, tuple[uuid.UUID, Direction]] = {}

            for piece_id, move_dir in remaining_moves_by_piece_id.copy().items():
                piece = self.get_piece_by_id(piece_id)
                new_pos = piece.position.offset_in_direction(move_dir)
                if self.has_piece_at_position(new_pos):
                    # someone is already there, we want to check whether they're pushing back
                    try:
                        other_piece_id, other_dir = collision_candidates[new_pos]
                    except KeyError:
                        # the other piece either isn't moving this time, or we just haven't encounterd it yet
                        collision_candidates[new_pos] = (piece_id, move_dir)
                        continue

                    if move_dir.get_opposite() != other_dir:
                        # the other piece isn't colliding with us. Either it's colliding with someone else, or it's going to push its pieces.
                        # Either way, we don't know yet what's going to happen, so we wait.
                        continue

                    # looks like we're colliding with the other piece
                    event.actions.append(moves_by_piece_id[piece_id])
                    event.actions.append(moves_by_piece_id[other_piece_id])
                    event.outcomes.append(
                        PushConflictOutcome.build(
                            PushConflictOutcomePayload(
                                piece_ids=[other_piece_id, piece_id],
                                collision_point=None,
                            )
                        )
                    )
                    # which means both moves are done
                    del remaining_moves_by_piece_id[piece_id]
                    del remaining_moves_by_piece_id[other_piece_id]
                    continue

                try:
                    candidates = trivial_move_candidates[new_pos]
                    candidates.append(piece_id)
                except KeyError:
                    trivial_move_candidates[new_pos] = [piece_id]

                del remaining_moves_by_piece_id[piece_id]

            for pos, piece_ids in trivial_move_candidates.items():
                if len(piece_ids) == 1:
                    piece_id = piece_ids[0]
                    event.actions.append(moves_by_piece_id[piece_id])
                    event.outcomes.append(
                        MoveOutcome.build(
                            MoveOutcomePayload(
                                piece_id=piece_id,
                                off_board=(not self.is_position_on_board(pos)),
                                new_position=pos,
                            )
                        )
                    )
                    self.set_piece_position(piece_id, pos)
                    continue

                event.actions.extend(
                    moves_by_piece_id[piece_id] for piece_id in piece_ids
                )
                event.outcomes.append(
                    MoveConflictOutcome.build(
                        MoveConflictOutcomePayload(
                            piece_ids=piece_ids, collision_point=pos
                        )
                    )
                )

            if event.is_empty():
                break
            yield event

    def _phase2_move(
        self,
        moves_by_piece_id: dict[uuid.UUID, PlayerMove],
        remaining_moves_by_piece_id: dict[uuid.UUID, Direction],
    ) -> TimelineEvent:
        """Phase 2 or the "push phase".

        Every remaining move passed to this function must be a push!
        """
        event = TimelineEvent(actions=[], outcomes=[])
        # mapping from pusher to victims, the last victim can be another moving piece, which might or might not be moving this round as well
        push_chains_by_piece_id: dict[uuid.UUID, list[uuid.UUID]] = {
            piece_id: [] for piece_id in remaining_moves_by_piece_id.keys()
        }
        push_outcomes: list[PushOutcomePayload] = []

        i = 0
        while True:
            found_complete_chain = False
            victim_pieces: dict[uuid.UUID, list[uuid.UUID]] = {}
            complete_push_chains: set[uuid.UUID] = set()

            for pusher_piece_id, victim_piece_ids in push_chains_by_piece_id.items():
                # as soon as we find the first complete chain we need to stop
                assert i == len(victim_piece_ids)
                push_dir = remaining_moves_by_piece_id[pusher_piece_id]
                if i > 0:
                    current_piece_id = victim_piece_ids[i - 1]
                else:
                    current_piece_id = pusher_piece_id
                current_piece = self.get_piece_by_id(current_piece_id)
                new_pos = current_piece.position.offset_in_direction(push_dir)
                new_piece = self.get_piece_at_position(new_pos)
                if new_piece is None:
                    found_complete_chain = True
                    complete_push_chains.add(pusher_piece_id)
                    continue
                new_piece_id = new_piece.piece_id
                victim_piece_ids.append(new_piece_id)
                if new_piece_id in push_chains_by_piece_id:
                    found_complete_chain = True
                    complete_push_chains.add(pusher_piece_id)
                    continue

                try:
                    other_pusher_piece_ids = victim_pieces[new_piece_id]
                except KeyError:
                    victim_pieces[new_piece_id] = [pusher_piece_id]
                else:
                    found_complete_chain = True
                    other_pusher_piece_ids.append(pusher_piece_id)

            if not found_complete_chain:
                i += 1
                continue

            for victim_piece_id, pusher_piece_ids in victim_pieces.items():
                if len(pusher_piece_ids) < 2:
                    # not a conflict
                    continue
                # push conflicts
                victim_piece = self.get_piece_by_id(victim_piece_id)
                event.actions.extend(
                    moves_by_piece_id[piece_id] for piece_id in pusher_piece_ids
                )
                event.outcomes.append(
                    PushConflictOutcome.build(
                        PushConflictOutcomePayload(
                            piece_ids=[victim_piece_id, *pusher_piece_ids],
                            collision_point=victim_piece.position,
                        )
                    )
                )
                for piece_id in pusher_piece_ids:
                    del remaining_moves_by_piece_id[piece_id]
                    complete_push_chains.discard(piece_id)

            for pusher_piece_id in complete_push_chains:
                push_dir = remaining_moves_by_piece_id[pusher_piece_id]
                victim_piece_ids = push_chains_by_piece_id[pusher_piece_id]
                if victim_piece_ids[-1] in complete_push_chains:
                    del victim_piece_ids[-1]

                push_outcome = PushOutcomePayload(
                    pusher_piece_id=pusher_piece_id,
                    victim_piece_ids=victim_piece_ids,
                    direction=push_dir,
                )
                push_outcomes.append(push_outcome)
                event.actions.append(moves_by_piece_id[pusher_piece_id])
                event.outcomes.append(PushOutcome.build(push_outcome))
                del remaining_moves_by_piece_id[pusher_piece_id]

            break

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
        while True:
            events.extend(
                self._phase1_moves(moves_by_piece_id, remaining_moves_by_piece_id)
            )
            if not remaining_moves_by_piece_id:
                break
            event = self._phase2_move(moves_by_piece_id, remaining_moves_by_piece_id)
            events.append(event)

        return events
