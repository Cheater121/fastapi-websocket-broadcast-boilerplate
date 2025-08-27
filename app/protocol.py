import time
from enum import StrEnum
from pydantic import BaseModel, Field

class MsgType(StrEnum):
    CHAT = "chat.message"
    DELIVERY = "chat.delivery"
    ACK = "system.ack"
    PING = "system.ping"
    PONG = "system.pong"
    ERROR = "system.error"

class BaseMsg(BaseModel):
    type: MsgType
    id: str | None = None
    version: int = 1

class ChatMessage(BaseMsg):
    type: MsgType = MsgType.CHAT
    room: str
    text: str

class Ping(BaseMsg):
    type: MsgType = MsgType.PING
    ts: float = Field(default_factory=lambda: time.time())

class Ack(BaseMsg):
    type: MsgType = MsgType.ACK
    ref: str | None = None
