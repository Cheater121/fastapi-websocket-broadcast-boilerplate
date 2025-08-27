from fastapi import FastAPI
from .lifespan import lifespan
from .websocket_routes import ws_router

app = FastAPI(lifespan=lifespan)
app.include_router(ws_router)
