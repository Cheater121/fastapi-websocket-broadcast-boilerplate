import json
import asyncio
from typing import Dict, Set, List
from fastapi import WebSocket
from .logger import logger

class RoomManager:
    """Хранит локальные WebSocket-соединения этого процесса для фактической отправки."""

    def __init__(self):
        self.rooms: Dict[str, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def add(self, room: str, ws: WebSocket) -> None:
        async with self._lock:
            self.rooms.setdefault(room, set()).add(ws)

    async def remove(self, room: str, ws: WebSocket) -> None:
        async with self._lock:
            conns = self.rooms.get(room)
            if not conns:
                return
            conns.discard(ws)
            if not conns:
                self.rooms.pop(room, None)

    async def snapshot(self, room: str) -> List[WebSocket]:
        async with self._lock:
            return list(self.rooms.get(room, ()))

    async def count(self, room: str) -> int:
        async with self._lock:
            return len(self.rooms.get(room, ()))

    async def send_local(self, room: str, payload: dict | str) -> None:
        data = json.dumps(payload) if not isinstance(payload, str) else payload
        targets = await self.snapshot(room)
        for ws in targets:
            try:
                await ws.send_text(data)
            except Exception as e:
                logger.warning("send_local failed: %s", e, exc_info=True)
                await self.remove(room, ws)

manager = RoomManager()
