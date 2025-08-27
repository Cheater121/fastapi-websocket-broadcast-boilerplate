import json
import uuid
import time
import asyncio
from fastapi import APIRouter, WebSocket
from fastapi import WebSocketDisconnect

from .auth import verify_token
from .config import (
    normalize_origin, ALLOWED_ORIGINS, ROOM_RE,
    PRESENCE_TTL, HEARTBEAT_INTERVAL, IDLE_TIMEOUT
)
from .protocol import MsgType, ChatMessage, Ping, Ack
from .managers import manager
from .subscriptions import SUBSCRIPTIONS
from . import state
from .logger import logger

ws_router = APIRouter()

@ws_router.websocket("/ws/{room}")
async def ws_room(ws: WebSocket, room: str):
    # 0) Проверка комнаты
    if not ROOM_RE.fullmatch(room):
        await ws.close(code=1008, reason="bad room")
        return

    # 1) Проверка Origin и JWT до accept()
    origin = normalize_origin(ws.headers.get("origin"))
    if ALLOWED_ORIGINS and (origin not in ALLOWED_ORIGINS):
        await ws.close(code=1008, reason="bad origin")
        return

    token = ws.query_params.get("token") or ws.cookies.get("access_token")
    claims = verify_token(token)
    if not claims:
        await ws.close(code=1008, reason="unauthorized")
        return

    user_id = str(claims.get("sub") or claims.get("user_id") or "anon")
    channel = f"room:{room}"
    presence_key = f"rt:presence:user:{user_id}:{room}"

    await ws.accept()

    # presence: ключ на (user, room) с TTL; обновляем на каждое действие
    async def touch_presence() -> None:
        if not state.rds:
            return
        await state.rds.set(presence_key, "1", ex=PRESENCE_TTL)

    await touch_presence()

    # Добавляем сокет и гарантируем подписку
    await manager.add(room, ws)
    await SUBSCRIPTIONS.ensure(room)

    stop = asyncio.Event()
    last_rx = time.time()

    async def reader():
        nonlocal last_rx
        try:
            while not stop.is_set():
                data = await ws.receive_json()
                last_rx = time.time()
                await touch_presence()

                try:
                    mtype = MsgType(data.get("type"))
                except Exception:
                    mtype = None

                if mtype is MsgType.CHAT:
                    msg = ChatMessage.model_validate(data)
                    mid = msg.id or uuid.uuid4().hex
                    payload = {
                        "type": MsgType.DELIVERY,
                        "room": room,
                        "user": user_id,
                        "text": msg.text,
                        "id": mid,
                        "ts": time.time(),
                    }
                    # Публикуем в канал комнаты
                    if state.broadcast:
                        await state.broadcast.publish(channel=channel, message=json.dumps(payload))
                elif mtype is MsgType.PING:
                    await ws.send_json(Ack(ref=(data.get("id") or uuid.uuid4().hex)).model_dump())
                elif mtype in (MsgType.ACK, MsgType.PONG):
                    # уже отметили активность выше
                    pass
                else:
                    await ws.send_json({"type": MsgType.ERROR, "error": "unknown_type"})
        except WebSocketDisconnect:
            logger.info("reader: client disconnected user=%s room=%s", user_id, room)
            stop.set()
        except Exception as e:
            logger.error("reader error: %s", e, exc_info=True)
            stop.set()

    async def heartbeat():
        try:
            while not stop.is_set():
                await asyncio.sleep(HEARTBEAT_INTERVAL)
                # прикладной ping
                try:
                    await ws.send_json(Ping().model_dump())
                except Exception as e:
                    logger.info("heartbeat send failed: %s", e)
                    stop.set()
                    return
                # idle-timeout
                if (time.time() - last_rx) > IDLE_TIMEOUT:
                    logger.info("idle timeout user=%s room=%s", user_id, room)
                    try:
                        await ws.close(code=1000, reason="idle timeout")
                    except Exception:
                        pass
                    stop.set()
                    return
        except WebSocketDisconnect:
            stop.set()
            return
        except Exception as e:
            logger.error("heartbeat error: %s", e, exc_info=True)
            stop.set()
            return

    # Совместный запуск задач с корректным cleanup
    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(reader())
            tg.create_task(heartbeat())
    except* Exception as eg:
        logger.debug("taskgroup exception group: %s", eg)
    finally:
        try:
            await manager.remove(room, ws)
        except Exception as e:
            logger.debug("manager.remove failed: %s", e, exc_info=True)
        try:
            if state.rds:
                await state.rds.delete(presence_key)
        except Exception as e:
            logger.debug("presence delete failed: %s", e, exc_info=True)
        try:
            await SUBSCRIPTIONS.maybe_stop(room)
        except Exception:
            pass
