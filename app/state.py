from typing import Optional
from broadcaster import Broadcast
import redis.asyncio as redis

broadcast: Optional[Broadcast] = None
rds: Optional[redis.Redis] = None
