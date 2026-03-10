import json
from datetime import timedelta

import redis

from app.core.config import settings


class RefreshSessionStore:
    def __init__(self) -> None:
        self._client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            decode_responses=True,
            socket_connect_timeout=1,
            socket_timeout=1,
        )
        # Redis 不可用时回落到内存，保证开发与测试可运行。
        self._memory_store: dict[str, dict] = {}

    @staticmethod
    def _key(jti: str) -> str:
        return f"auth:refresh:{jti}"

    def save(self, *, jti: str, user_id: int, ttl_seconds: int) -> None:
        payload = json.dumps({"uid": user_id})
        key = self._key(jti)
        try:
            self._client.set(name=key, value=payload, ex=ttl_seconds)
        except redis.RedisError:
            self._memory_store[key] = {"uid": user_id}

    def exists(self, *, jti: str) -> bool:
        key = self._key(jti)
        try:
            return bool(self._client.exists(key))
        except redis.RedisError:
            return key in self._memory_store

    def revoke(self, *, jti: str) -> None:
        key = self._key(jti)
        try:
            self._client.delete(key)
        except redis.RedisError:
            self._memory_store.pop(key, None)


def refresh_token_ttl_seconds() -> int:
    return int(timedelta(days=settings.jwt_refresh_expire_days).total_seconds())
