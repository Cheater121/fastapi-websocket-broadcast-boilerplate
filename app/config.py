import os
import re
from urllib.parse import urlparse

# ---------- Конфигурация окружения ----------
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
JWT_SECRET = os.getenv("JWT_SECRET", "change-me")
JWT_ALG = os.getenv("JWT_ALG", "HS256")

# Живость/присутствие
PRESENCE_TTL = int(os.getenv("PRESENCE_TTL", "60"))  # сек
HEARTBEAT_INTERVAL = int(os.getenv("HEARTBEAT_INTERVAL", "25"))
IDLE_TIMEOUT = int(os.getenv("IDLE_TIMEOUT", "70"))

# Валидация имени комнаты
ROOM_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")

def normalize_origin(origin: str | None) -> str | None:
    """Канонизирует Origin (scheme+host[:port], без стандартных портов)."""
    if not origin:
        return None
    p = urlparse(origin)
    if not p.scheme or not p.hostname:
        return None
    host = p.hostname.lower()
    port = p.port
    default_port = 443 if p.scheme == "https" else 80
    if port in (None, default_port):
        return f"{p.scheme}://{host}"
    return f"{p.scheme}://{host}:{port}"

# ALLOWED_ORIGINS: список origin'ов (scheme+host[:port]), через запятую
_ALO_RAW = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o.strip()]
ALLOWED_ORIGINS: set[str] = {o for o in (normalize_origin(x) for x in _ALO_RAW) if o}
