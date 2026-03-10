import json
from datetime import datetime, timezone
from uuid import uuid4

import redis

from app.core.config import settings


class UploadSessionStore:
    def __init__(self) -> None:
        self._client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            decode_responses=True,
            socket_connect_timeout=1,
            socket_timeout=1,
        )
        self._memory_store: dict[str, dict] = {}

    @staticmethod
    def _key(upload_id: str) -> str:
        return f"upload:session:{upload_id}"

    def create_session(
        self,
        *,
        owner_id: int,
        file_name: str,
        total_size: int,
        chunk_size: int,
        total_chunks: int,
        mime_type: str,
        file_hash: str | None,
    ) -> dict:
        upload_id = uuid4().hex
        session = {
            "upload_id": upload_id,
            "owner_id": owner_id,
            "file_name": file_name,
            "total_size": total_size,
            "chunk_size": chunk_size,
            "total_chunks": total_chunks,
            "mime_type": mime_type,
            "file_hash": file_hash,
            "status": "uploading",
            "uploaded_chunks": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.save_session(upload_id=upload_id, session=session)
        return session

    def save_session(self, *, upload_id: str, session: dict) -> None:
        key = self._key(upload_id)
        payload = json.dumps(session)
        try:
            self._client.set(name=key, value=payload, ex=settings.upload_session_ttl_seconds)
        except redis.RedisError:
            self._memory_store[key] = session

    def get_session(self, *, upload_id: str) -> dict | None:
        key = self._key(upload_id)
        try:
            raw = self._client.get(key)
            if raw is None:
                return None
            return json.loads(raw)
        except redis.RedisError:
            return self._memory_store.get(key)

    def mark_chunk_uploaded(self, *, upload_id: str, chunk_index: int) -> dict | None:
        session = self.get_session(upload_id=upload_id)
        if not session:
            return None

        chunks = set(session.get("uploaded_chunks", []))
        chunks.add(chunk_index)
        session["uploaded_chunks"] = sorted(chunks)
        self.save_session(upload_id=upload_id, session=session)
        return session


upload_session_store = UploadSessionStore()
