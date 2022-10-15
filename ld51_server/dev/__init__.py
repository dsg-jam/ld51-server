from fastapi import APIRouter

from . import lobby, protocol

router = APIRouter(prefix="/dev-tools", tags=["dev-tools"])

router.include_router(lobby.router)
router.include_router(protocol.router)
