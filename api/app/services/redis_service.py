# app/services/redis_service.py
import redis.asyncio as aioredis
from app.config import settings
import json
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

_redis: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = await aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis


async def close_redis():
    global _redis
    if _redis:
        await _redis.close()
        _redis = None
        logger.info("Redis connection closed.")


# ── Cache helpers ──────────────────────────────────────────────────────────────

async def cache_set(key: str, value: Any, ttl: int = 1800) -> None:
    r = await get_redis()
    await r.setex(key, ttl, json.dumps(value, default=str))


async def cache_get(key: str) -> Optional[Any]:
    r = await get_redis()
    data = await r.get(key)
    return json.loads(data) if data else None


async def cache_delete(key: str) -> None:
    r = await get_redis()
    await r.delete(key)


# ── Rate Limiting helpers ──────────────────────────────────────────────────────

async def check_rate_limit(key: str, limit: int, window: int) -> tuple[bool, int, int]:
    """
    Sliding-window rate limiter.
    Returns: (allowed, remaining, retry_after)
    """
    r = await get_redis()
    current = await r.incr(key)
    if current == 1:
        await r.expire(key, window)
    ttl = await r.ttl(key)
    remaining = max(0, limit - current)
    allowed = current <= limit
    return allowed, remaining, ttl


# ── WebSocket Session ──────────────────────────────────────────────────────────

async def register_ws_session(user_id: str, connection_id: str) -> None:
    r = await get_redis()
    key = f"websocket:session:{user_id}"
    from datetime import datetime, timezone
    await r.hset(key, mapping={
        "connection_id": connection_id,
        "connected_at": datetime.now(timezone.utc).isoformat(),
        "last_ping": datetime.now(timezone.utc).isoformat(),
    })
    await r.expire(key, 3600)


async def remove_ws_session(user_id: str) -> None:
    r = await get_redis()
    await r.delete(f"websocket:session:{user_id}")


async def publish_order_update(user_id: str, message: dict) -> None:
    """Publish a message to the user's order update channel."""
    r = await get_redis()
    channel = f"orders:{user_id}"
    await r.publish(channel, json.dumps(message, default=str))
