from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import dev, game

app = FastAPI(
    title="LD51 Server",
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
