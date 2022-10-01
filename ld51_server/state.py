import uuid
from .models import PlayerPiecePosition

class BoardState:
    pieces: list[PlayerPiecePosition]
