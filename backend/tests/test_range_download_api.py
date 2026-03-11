from fastapi.testclient import TestClient

from app.db import SessionLocal
from app.models.file_object import FileObject
from app.main import app
from app.services.object_storage import object_storage_service


def _prepare_uploaded_file(
    client: TestClient,
    *,
    email: str,
    username: str,
    file_name: str = "range.txt",
) -> tuple[str, int, bytes]:
    content = b"range-download-content-demo"
    chunk_size = 6
    chunks = [content[i : i + chunk_size] for i in range(0, len(content), chunk_size)]

    client.post(
        "/auth/register",
        json={"email": email, "username": username, "password": "Passw0rd!"},
    )
    login = client.post("/auth/login", json={"account": username, "password": "Passw0rd!"})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    create = client.post(
        "/upload/sessions",
        headers=headers,
        json={
            "file_name": file_name,
            "total_size": len(content),
            "chunk_size": chunk_size,
            "total_chunks": len(chunks),
            "mime_type": "text/plain",
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
    file_id = done.json()["file_id"]
    return token, file_id, content


def test_download_requires_auth() -> None:
    with TestClient(app) as client:
        response = client.get("/files/1/download")
        assert response.status_code == 401


def test_download_full_and_range() -> None:
    with TestClient(app) as client:
        token, file_id, content = _prepare_uploaded_file(client, email="range1@test.com", username="range001")
        headers = {"Authorization": f"Bearer {token}"}

        full = client.get(f"/files/{file_id}/download", headers=headers)
        assert full.status_code == 200
        assert full.content == content

        partial = client.get(
            f"/files/{file_id}/download",
            headers={**headers, "Range": "bytes=5-10"},
        )
        assert partial.status_code == 206
        assert partial.content == content[5:11]
        assert partial.headers["content-range"] == f"bytes 5-10/{len(content)}"

        invalid = client.get(
            f"/files/{file_id}/download",
            headers={**headers, "Range": f"bytes={len(content)+10}-{len(content)+20}"},
        )
        assert invalid.status_code == 416


def test_download_forbidden_for_other_user() -> None:
    with TestClient(app) as client:
        owner_token, file_id, _ = _prepare_uploaded_file(client, email="owner@test.com", username="owner001")
        _ = owner_token

        client.post(
            "/auth/register",
            json={"email": "other@test.com", "username": "other001", "password": "Passw0rd!"},
        )
        other_login = client.post("/auth/login", json={"account": "other001", "password": "Passw0rd!"})
        other_headers = {"Authorization": f"Bearer {other_login.json()['access_token']}"}

        forbidden = client.get(f"/files/{file_id}/download", headers=other_headers)
        assert forbidden.status_code == 403


def test_download_with_non_ascii_filename() -> None:
    with TestClient(app) as client:
        token, file_id, content = _prepare_uploaded_file(
            client,
            email="cnrange@test.com",
            username="cnrange001",
            file_name="中文报告.txt",
        )
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get(f"/files/{file_id}/download", headers=headers)
        assert response.status_code == 200
        assert response.content == content
        assert "filename*=" in response.headers["content-disposition"]


def test_download_returns_404_when_object_missing() -> None:
    with TestClient(app) as client:
        token, file_id, _ = _prepare_uploaded_file(client, email="missing@test.com", username="missing001")
        headers = {"Authorization": f"Bearer {token}"}

        with SessionLocal() as db:
            file_record = db.get(FileObject, file_id)
            assert file_record is not None
            object_storage_service.delete_object(object_key=file_record.object_key)

        response = client.get(f"/files/{file_id}/download", headers=headers)
        assert response.status_code == 404
        assert response.json()["detail"] == "文件内容不存在"


def test_download_reads_legacy_fallback_path() -> None:
    with TestClient(app) as client:
        token, file_id, content = _prepare_uploaded_file(
            client,
            email="legacy@test.com",
            username="legacy001",
            file_name="legacy.txt",
        )
        headers = {"Authorization": f"Bearer {token}"}

        with SessionLocal() as db:
            file_record = db.get(FileObject, file_id)
            assert file_record is not None

            candidates = object_storage_service._fallback_candidates(file_record.object_key)
            if len(candidates) < 2:
                return
            primary = candidates[0]
            legacy = candidates[-1]

            primary.parent.mkdir(parents=True, exist_ok=True)
            primary.write_bytes(content)
            if legacy.exists():
                legacy.unlink()
            legacy.parent.mkdir(parents=True, exist_ok=True)
            legacy.write_bytes(content)
            primary.unlink()

        response = client.get(f"/files/{file_id}/download", headers=headers)
        assert response.status_code == 200
        assert response.content == content


def test_download_recovers_from_legacy_object_key_path_mismatch() -> None:
    with TestClient(app) as client:
        token, file_id, content = _prepare_uploaded_file(
            client,
            email="legacyrename@test.com",
            username="legacyrename001",
            file_name="logs/readme.txt",
        )
        headers = {"Authorization": f"Bearer {token}"}

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

        response = client.get(f"/files/{file_id}/download", headers=headers)
        assert response.status_code == 200
        assert response.content == content

        with SessionLocal() as db:
            file_record = db.get(FileObject, file_id)
            assert file_record is not None
            assert file_record.object_key.endswith("/log/readme.txt")
