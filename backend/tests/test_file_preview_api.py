from fastapi.testclient import TestClient

from app.db import SessionLocal
from app.models.file_object import FileObject
from app.main import app
from app.services.object_storage import object_storage_service


def _upload_file(
    client: TestClient,
    *,
    token: str,
    file_name: str,
    mime_type: str,
    content: bytes,
    chunk_size: int = 6,
) -> int:
    chunks = [content[i : i + chunk_size] for i in range(0, len(content), chunk_size)]
    headers = {"Authorization": f"Bearer {token}"}

    create = client.post(
        "/upload/sessions",
        headers=headers,
        json={
            "file_name": file_name,
            "total_size": len(content),
            "chunk_size": chunk_size,
            "total_chunks": len(chunks),
            "mime_type": mime_type,
        },
    )
    upload_id = create.json()["upload_id"]

    for index, part in enumerate(chunks):
        client.put(
            f"/upload/sessions/{upload_id}/chunks/{index}",
            headers=headers,
            files={"chunk": ("chunk.part", part, "application/octet-stream")},
        )

    done = client.post(f"/upload/sessions/{upload_id}/complete", headers=headers)
    return done.json()["file_id"]


def test_preview_requires_auth() -> None:
    with TestClient(app) as client:
        response = client.get("/files/1/preview")
        assert response.status_code == 401


def test_preview_supported_and_unsupported_type() -> None:
    with TestClient(app) as client:
        client.post(
            "/auth/register",
            json={"email": "preview@test.com", "username": "preview001", "password": "Passw0rd!"},
        )
        login = client.post("/auth/login", json={"account": "preview001", "password": "Passw0rd!"})
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        txt_id = _upload_file(
            client,
            token=token,
            file_name="note.txt",
            mime_type="text/plain",
            content=b"hello preview",
        )
        zip_id = _upload_file(
            client,
            token=token,
            file_name="pack.zip",
            mime_type="application/zip",
            content=b"PK\\x03\\x04zip",
        )

        preview_ok = client.get(f"/files/{txt_id}/preview", headers=headers)
        assert preview_ok.status_code == 200
        assert preview_ok.text == "hello preview"

        preview_bad = client.get(f"/files/{zip_id}/preview", headers=headers)
        assert preview_bad.status_code == 400


def test_preview_forbidden_for_other_user() -> None:
    with TestClient(app) as client:
        client.post(
            "/auth/register",
            json={"email": "ownerp@test.com", "username": "ownerp001", "password": "Passw0rd!"},
        )
        owner_login = client.post("/auth/login", json={"account": "ownerp001", "password": "Passw0rd!"})
        owner_token = owner_login.json()["access_token"]

        file_id = _upload_file(
            client,
            token=owner_token,
            file_name="owner.txt",
            mime_type="text/plain",
            content=b"owner content",
        )

        client.post(
            "/auth/register",
            json={"email": "otherp@test.com", "username": "otherp001", "password": "Passw0rd!"},
        )
        other_login = client.post("/auth/login", json={"account": "otherp001", "password": "Passw0rd!"})
        other_headers = {"Authorization": f"Bearer {other_login.json()['access_token']}"}

        forbidden = client.get(f"/files/{file_id}/preview", headers=other_headers)
        assert forbidden.status_code == 403


def test_preview_text_extension_with_octet_stream_supported() -> None:
    with TestClient(app) as client:
        client.post(
            "/auth/register",
            json={"email": "octet@test.com", "username": "octet001", "password": "Passw0rd!"},
        )
        login = client.post("/auth/login", json={"account": "octet001", "password": "Passw0rd!"})
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        txt_id = _upload_file(
            client,
            token=token,
            file_name="notes/runtime.log",
            mime_type="application/octet-stream",
            content=b"log line one",
        )

        preview = client.get(f"/files/{txt_id}/preview", headers=headers)
        assert preview.status_code == 200
        assert preview.text == "log line one"


def test_preview_returns_404_when_object_missing() -> None:
    with TestClient(app) as client:
        client.post(
            "/auth/register",
            json={"email": "missingp@test.com", "username": "missingp001", "password": "Passw0rd!"},
        )
        login = client.post("/auth/login", json={"account": "missingp001", "password": "Passw0rd!"})
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        file_id = _upload_file(
            client,
            token=token,
            file_name="missing.txt",
            mime_type="text/plain",
            content=b"to be removed",
        )

        with SessionLocal() as db:
            file_record = db.get(FileObject, file_id)
            assert file_record is not None
            object_storage_service.delete_object(object_key=file_record.object_key)

        preview = client.get(f"/files/{file_id}/preview", headers=headers)
        assert preview.status_code == 404
        assert preview.json()["detail"] == "文件内容不存在"


def test_preview_recovers_from_legacy_object_key_path_mismatch() -> None:
    with TestClient(app) as client:
        client.post(
            "/auth/register",
            json={"email": "previewlegacy@test.com", "username": "previewlegacy001", "password": "Passw0rd!"},
        )
        login = client.post("/auth/login", json={"account": "previewlegacy001", "password": "Passw0rd!"})
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        file_id = _upload_file(
            client,
            token=token,
            file_name="logs/readme.txt",
            mime_type="text/plain",
            content=b"preview me",
        )

        with SessionLocal() as db:
            file_record = db.get(FileObject, file_id)
            assert file_record is not None
            original_key = file_record.object_key
            renamed_key = f"{original_key.rsplit('/', 2)[0]}/log/readme.txt"

            source = object_storage_service._find_existing_fallback_path(original_key)
            target = object_storage_service._primary_fallback_path(renamed_key)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.read_bytes())
            source.unlink()

            file_record.file_name = "log/readme.txt"
            db.add(file_record)
            db.commit()

        preview = client.get(f"/files/{file_id}/preview", headers=headers)
        assert preview.status_code == 200
        assert preview.text == "preview me"


def test_preview_prefers_local_fallback_before_minio_probe(monkeypatch) -> None:
    with TestClient(app) as client:
        client.post(
            "/auth/register",
            json={"email": "previewlocal@test.com", "username": "previewlocal001", "password": "Passw0rd!"},
        )
        login = client.post("/auth/login", json={"account": "previewlocal001", "password": "Passw0rd!"})
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        file_id = _upload_file(
            client,
            token=token,
            file_name="logs/local-readme.txt",
            mime_type="text/plain",
            content=b"local preview",
        )

        def fail_minio_probe() -> None:
            raise AssertionError("存在本地对象时不应先探测 MinIO")

        monkeypatch.setattr(object_storage_service, "_ensure_bucket", fail_minio_probe)

        preview = client.get(f"/files/{file_id}/preview", headers=headers)
        assert preview.status_code == 200
        assert preview.text == "local preview"


def test_upload_keeps_local_fallback_copy_for_preview() -> None:
    with TestClient(app) as client:
        client.post(
            "/auth/register",
            json={"email": "previewcopy@test.com", "username": "previewcopy001", "password": "Passw0rd!"},
        )
        login = client.post("/auth/login", json={"account": "previewcopy001", "password": "Passw0rd!"})
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        file_id = _upload_file(
            client,
            token=token,
            file_name="logs/fallback-copy.txt",
            mime_type="text/plain",
            content=b"fallback copy",
        )

        with SessionLocal() as db:
            file_record = db.get(FileObject, file_id)
            assert file_record is not None
            fallback = object_storage_service._primary_fallback_path(file_record.object_key)
            assert fallback.exists()
            assert fallback.read_bytes() == b"fallback copy"
