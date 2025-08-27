import json
import asyncio
from .logger import logger
from .managers import manager
from .protocol import MsgType
from . import state

class RoomSubscriptions:
    """Задачи подписки на каналы Redis по комнатам (уровень процесса)."""

    def __init__(self):
        self._tasks: dict[str, asyncio.Task] = {}
        self._lock = asyncio.Lock()

    async def ensure(self, room: str) -> None:
        async with self._lock:
            task = self._tasks.get(room)
            if task and not task.done():
                return
            self._tasks[room] = asyncio.create_task(self._runner(room), name=f"sub:{room}")

    async def maybe_stop(self, room: str) -> None:
        if await manager.count(room) > 0:
            return
        async with self._lock:
            task = self._tasks.pop(room, None)
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                except Exception:
                    logger.debug("subscriber task error on cancel", exc_info=True)

    async def cancel_all(self) -> None:
        async with self._lock:
            tasks = list(self._tasks.values())
            self._tasks.clear()
        for t in tasks:
            t.cancel()
        for t in tasks:
            try:
                await t
            except asyncio.CancelledError:
                pass
            except Exception:
                logger.debug("subscriber task error on cancel_all", exc_info=True)

    async def _runner(self, room: str) -> None:
        channel = f"room:{room}"
        backoff = 1.0
        while True:
            if await manager.count(room) == 0:
                logger.info("subscriber: room %s empty -> stop", room)
                return
            try:
                if not state.broadcast:
                    raise RuntimeError("Broadcast is not initialized")
                async with state.broadcast.subscribe(channel=channel) as sub:
                    logger.info("subscriber: subscribed to %s", channel)
                    backoff = 1.0
                    async for event in sub:
                        if await manager.count(room) == 0:
                            logger.info("subscriber: room %s empty during stream -> stop", room)
                            return
                        try:
                            payload = json.loads(event.message)
                        except Exception:
                            payload = {"type": MsgType.ERROR, "error": "bad_payload"}
                        await manager.send_local(room, payload)
            except asyncio.CancelledError:
                logger.debug("subscriber: cancelled for %s", room)
                raise
            except Exception as e:
                logger.warning(
                    "subscriber error for %s: %s; retry in %.1fs",
                    room, e, backoff, exc_info=True
                )
                await asyncio.sleep(min(backoff, 10.0))
                backoff = min(backoff * 2.0, 10.0)

SUBSCRIPTIONS = RoomSubscriptions()
