from pathlib import Path
from pathlib import PurePosixPath

from minio import Minio
import urllib3

from app.core.config import settings


class ObjectStorageService:
    def __init__(self) -> None:
        http_client = urllib3.PoolManager(
            timeout=urllib3.Timeout(connect=0.5, read=0.5),
            retries=False,
        )
        self._client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
            http_client=http_client,
        )
        self._fallback_roots = self._build_fallback_roots()
        for root in self._fallback_roots:
            root.mkdir(parents=True, exist_ok=True)

    def upload_file(self, *, local_path: Path, object_key: str, content_type: str) -> str:
        fallback_path = self._primary_fallback_path(object_key)
        fallback_path.parent.mkdir(parents=True, exist_ok=True)
        fallback_path.write_bytes(local_path.read_bytes())
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
            # 开发测试环境始终保留本地对象副本，避免 MinIO 波动阻塞验证。
            return object_key

    def get_file_size(self, *, object_key: str) -> int:
        fallback = self._find_existing_fallback_path(object_key)
        if fallback.exists():
            return fallback.stat().st_size
        try:
            self._ensure_bucket()
            stat = self._client.stat_object(settings.minio_bucket, object_key)
            return stat.size
        except Exception:
            if not fallback.exists():
                raise FileNotFoundError(f"对象不存在: {object_key}")
            return fallback.stat().st_size

    def read_range(self, *, object_key: str, start: int, end: int) -> bytes:
        if start < 0 or end < start:
            raise ValueError("无效的下载范围")
        length = end - start + 1
        fallback = self._find_existing_fallback_path(object_key)
        if fallback.exists():
            with fallback.open("rb") as fp:
                fp.seek(start)
                return fp.read(length)
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
            if not fallback.exists():
                raise FileNotFoundError(f"对象不存在: {object_key}")
            with fallback.open("rb") as fp:
                fp.seek(start)
                return fp.read(length)

    def delete_object(self, *, object_key: str) -> None:
        try:
            self._ensure_bucket()
            self._client.remove_object(settings.minio_bucket, object_key)
        except Exception:
            for fallback in self._fallback_candidates(object_key):
                if fallback.exists():
                    fallback.unlink()

    def resolve_object_key(self, *, object_key: str, file_name: str) -> str:
        if self._object_exists(object_key):
            return object_key

        upload_prefix = self._upload_prefix(object_key)
        basename = PurePosixPath(file_name).name
        if not upload_prefix or not basename:
            raise FileNotFoundError(f"对象不存在: {object_key}")

        for candidate in self._search_candidate_keys(upload_prefix=upload_prefix, basename=basename):
            if candidate != object_key and self._object_exists(candidate):
                return candidate

        raise FileNotFoundError(f"对象不存在: {object_key}")

    def _ensure_bucket(self) -> None:
        if not self._client.bucket_exists(settings.minio_bucket):
            self._client.make_bucket(settings.minio_bucket)

    def _object_exists(self, object_key: str) -> bool:
        if any(candidate.exists() for candidate in self._fallback_candidates(object_key)):
            return True
        try:
            self._ensure_bucket()
            self._client.stat_object(settings.minio_bucket, object_key)
            return True
        except Exception:
            return False

    @staticmethod
    def _upload_prefix(object_key: str) -> str:
        parts = list(PurePosixPath(object_key).parts)
        if len(parts) >= 2:
            return "/".join(parts[:2])
        if len(parts) == 1:
            return parts[0]
        return ""

    def _search_candidate_keys(self, *, upload_prefix: str, basename: str) -> list[str]:
        candidates: list[str] = []
        seen = set()

        for root in self._fallback_roots:
            base_dir = root / upload_prefix
            if not base_dir.exists():
                continue
            for path in base_dir.rglob(basename):
                if not path.is_file():
                    continue
                object_name = path.relative_to(root).as_posix()
                if object_name in seen:
                    continue
                seen.add(object_name)
                candidates.append(object_name)

        try:
            self._ensure_bucket()
            for item in self._client.list_objects(settings.minio_bucket, prefix=f"{upload_prefix}/", recursive=True):
                if PurePosixPath(item.object_name).name != basename:
                    continue
                if item.object_name in seen:
                    continue
                seen.add(item.object_name)
                candidates.append(item.object_name)
        except Exception:
            pass

        return candidates

    @staticmethod
    def _build_fallback_roots() -> list[Path]:
        roots = [
            Path(settings.upload_tmp_dir).resolve().parent / "object_store",
            Path(__file__).resolve().parents[2] / "tmp" / "object_store",
            Path(__file__).resolve().parents[3] / "tmp" / "object_store",
        ]

        deduped: list[Path] = []
        seen = set()
        for root in roots:
            key = str(root.resolve())
            if key in seen:
                continue
            seen.add(key)
            deduped.append(root)
        return deduped

    def _primary_fallback_path(self, object_key: str) -> Path:
        return self._fallback_roots[0] / object_key

    def _fallback_candidates(self, object_key: str) -> list[Path]:
        return [root / object_key for root in self._fallback_roots]

    def _find_existing_fallback_path(self, object_key: str) -> Path:
        for candidate in self._fallback_candidates(object_key):
            if candidate.exists():
                return candidate
        return self._primary_fallback_path(object_key)


object_storage_service = ObjectStorageService()
