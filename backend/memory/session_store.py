"""Session storage in Redis. Survives backend restarts.

Sessions are stored as JSON with a TTL of 24 hours.
Keys: runa:session:{session_id} and runa:checkin:{user_id}
"""

import json
import redis.asyncio as redis


class SessionStore:
    """Async Redis-backed session storage."""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = redis.from_url(redis_url, decode_responses=True)

    async def close(self):
        await self.redis.aclose()

    # ── Onboarding sessions ──

    async def save_onboarding(self, session_id: str, data: dict) -> None:
        key = f"runa:session:{session_id}"
        await self.redis.set(key, json.dumps(data, ensure_ascii=False))

    async def get_onboarding(self, session_id: str) -> dict | None:
        key = f"runa:session:{session_id}"
        raw = await self.redis.get(key)
        if raw:
            return json.loads(raw)
        return None

    # ── Checkin conversation history ──

    async def save_checkin_history(self, user_id: str, messages: list[dict]) -> None:
        key = f"runa:checkin:{user_id}"
        # Keep last 20 messages
        trimmed = messages[-20:] if len(messages) > 20 else messages
        await self.redis.set(key, json.dumps(trimmed, ensure_ascii=False))

    async def get_checkin_history(self, user_id: str) -> list[dict]:
        key = f"runa:checkin:{user_id}"
        raw = await self.redis.get(key)
        if raw:
            return json.loads(raw)
        return []

    # ── Generic session (sphere chats, etc.) ──

    async def save_session(self, session_key: str, messages: list[dict]) -> None:
        key = f"runa:session:{session_key}"
        trimmed = messages[-20:] if len(messages) > 20 else messages
        await self.redis.set(key, json.dumps(trimmed, ensure_ascii=False))

    async def get_session(self, session_key: str) -> list[dict]:
        key = f"runa:session:{session_key}"
        raw = await self.redis.get(key)
        if raw:
            return json.loads(raw)
        return []
