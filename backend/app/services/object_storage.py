from pathlib import Path

from minio import Minio

from app.core.config import settings


class ObjectStorageService:
    def __init__(self) -> None:
        self._client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )
        self._fallback_root = Path(settings.upload_tmp_dir).resolve().parent / "object_store"
        self._fallback_root.mkdir(parents=True, exist_ok=True)

    def upload_file(self, *, local_path: Path, object_key: str, content_type: str) -> str:
        try:
            self._ensure_bucket()
            self._client.fput_object(
                bucket_name=settings.minio_bucket,
                object_name=object_key,
                file_path=str(local_path),
                content_type=content_type,
            )
            return object_key
        except Exception:
            # 开发测试回落本地对象目录，避免无 MinIO 时阻塞验证。
            fallback_path = self._fallback_root / object_key
            fallback_path.parent.mkdir(parents=True, exist_ok=True)
            fallback_path.write_bytes(local_path.read_bytes())
            return object_key

    def get_file_size(self, *, object_key: str) -> int:
        try:
            self._ensure_bucket()
            stat = self._client.stat_object(settings.minio_bucket, object_key)
            return stat.size
        except Exception:
            fallback = self._fallback_path(object_key)
            if not fallback.exists():
                raise FileNotFoundError(f"对象不存在: {object_key}")
            return fallback.stat().st_size

    def read_range(self, *, object_key: str, start: int, end: int) -> bytes:
        if start < 0 or end < start:
            raise ValueError("无效的下载范围")
        length = end - start + 1
        try:
            self._ensure_bucket()
            response = self._client.get_object(
                bucket_name=settings.minio_bucket,
                object_name=object_key,
                offset=start,
                length=length,
            )
            try:
                return response.read()
            finally:
                response.close()
                response.release_conn()
        except Exception:
            fallback = self._fallback_path(object_key)
            if not fallback.exists():
                raise FileNotFoundError(f"对象不存在: {object_key}")
            with fallback.open("rb") as fp:
                fp.seek(start)
                return fp.read(length)

    def _ensure_bucket(self) -> None:
        if not self._client.bucket_exists(settings.minio_bucket):
            self._client.make_bucket(settings.minio_bucket)

    def _fallback_path(self, object_key: str) -> Path:
        return self._fallback_root / object_key


object_storage_service = ObjectStorageService()
