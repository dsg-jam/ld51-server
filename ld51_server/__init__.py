import importlib.metadata

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import dev, game

PROJECT_NAME = "ld51_server"

try:
    VERSION = importlib.metadata.version(PROJECT_NAME)
except importlib.metadata.PackageNotFoundError:
    VERSION = "unknown"  # type: ignore

app = FastAPI(
    title="LD51 Server",
    version=VERSION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(game.router)
app.include_router(dev.router)
