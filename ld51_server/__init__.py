from fastapi import FastAPI

from . import dev, game

app = FastAPI(
    title="LD51 Server",
)

app.include_router(game.router)
app.include_router(dev.router)
