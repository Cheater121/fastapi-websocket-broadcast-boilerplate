from contextlib import asynccontextmanager
from broadcaster import Broadcast
import redis.asyncio as redis
from . import state
from .subscriptions import SUBSCRIPTIONS
from .config import REDIS_URL
from .logger import logger

@asynccontextmanager
async def lifespan(app):
    # Инициализация Redis и Broadcast
    state.rds = await redis.from_url(REDIS_URL, decode_responses=True)
    state.broadcast = Broadcast(REDIS_URL)
    await state.broadcast.connect()
    try:
        yield
    finally:
        try:
            await SUBSCRIPTIONS.cancel_all()
        except Exception:
            logger.debug("cancel_all failed", exc_info=True)
        try:
            if state.broadcast:
                await state.broadcast.disconnect()
        finally:
            state.broadcast = None
        try:
            if state.rds:
                await state.rds.aclose()
        finally:
            state.rds = None
