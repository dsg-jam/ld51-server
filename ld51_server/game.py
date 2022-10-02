import dataclasses
import uuid

from .models import (
    Direction,
    PlayerMove,
    PlayerPiecePosition,
    Position,
    PushConflictOutcomePayload,
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


class BoardState:
    _piece_by_position: dict[Position, PieceInformation]

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

    def perform_player_moves(self, moves: list[PlayerMove]) -> None:
        # TODO: verify player moves:
        #   - piece must exist and be owned by the player

        remaining_moves_by_piece: dict[uuid.UUID, tuple[Position, Direction]] = {}
        # populate remaining moves
        for move in moves:
            move_dir = move.action.as_direction()
            if move_dir is None:
                continue
            piece_id = move.piece_id
            piece = self.get_piece_by_id(piece_id)
            remaining_moves_by_piece[piece_id] = (piece.position, move_dir)

        while remaining_moves_by_piece:
            # map target position to pieces that want to move to that spot
            trivial_move_candidates: dict[Position, list[uuid.UUID]] = {}
            # map position to piece id and push direction
            collision_candidates: dict[Position, tuple[uuid.UUID, Direction]] = {}
            confirmed_collisions = list[PushConflictOutcomePayload] = []

            # phase 1: moves and collisions
            for piece_id, (
                piece_pos,
                move_dir,
            ) in remaining_moves_by_piece.copy().items():
                new_pos = piece_pos.offset_in_direction(move_dir)
                if new_pos in self._piece_by_position:
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
                    confirmed_collisions.append(
                        PushConflictOutcomePayload(
                            piece_a=other_piece_id, piece_b=piece_id
                        )
                    )
                    # which means both moves are done
                    del remaining_moves_by_piece[piece_id]
                    del remaining_moves_by_piece[other_piece_id]
                    continue

                try:
                    candidates = trivial_move_candidates[new_pos]
                    candidates.append(piece_id)
                except KeyError:
                    candidates[new_pos] = [piece_id]

                del remaining_moves_by_piece[piece_id]

            # TODO: everything in trivial_move_candidates is now either a move or a move conflict (depending on the number of piece_ids)

            # phase 2: perform shortest push
            # TODO: use collision_candidates to check push chains (also need to check for collisions)
