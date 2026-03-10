from fastapi.testclient import TestClient

from app.db import SessionLocal
from app.models.file_object import FileObject
from app.main import app


def _prepare_uploaded_file(client: TestClient, *, email: str, username: str) -> tuple[str, int]:
    content = b"recycle-flow-content"
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
            "file_name": "recycle.txt",
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
    return token, done.json()["file_id"]


def test_recycle_requires_auth() -> None:
    with TestClient(app) as client:
        response = client.get("/recycle/files")
        assert response.status_code == 401


def test_soft_delete_restore_and_purge_flow() -> None:
    with TestClient(app) as client:
        token, file_id = _prepare_uploaded_file(client, email="recycle1@test.com", username="recycle001")
        headers = {"Authorization": f"Bearer {token}"}

        delete_resp = client.delete(f"/files/{file_id}", headers=headers)
        assert delete_resp.status_code == 200
        assert delete_resp.json()["status"] == "deleted"

        files_list = client.get("/files", headers=headers)
        assert files_list.status_code == 200
        assert files_list.json()["total"] == 0

        recycle_list = client.get("/recycle/files", headers=headers)
        assert recycle_list.status_code == 200
        assert recycle_list.json()["total"] == 1

        restore_resp = client.post(f"/recycle/files/{file_id}/restore", headers=headers)
        assert restore_resp.status_code == 200
        assert restore_resp.json()["status"] == "active"

        recycle_after_restore = client.get("/recycle/files", headers=headers)
        assert recycle_after_restore.status_code == 200
        assert recycle_after_restore.json()["total"] == 0

        delete_again = client.delete(f"/files/{file_id}", headers=headers)
        assert delete_again.status_code == 200

        purge_resp = client.delete(f"/recycle/files/{file_id}/purge", headers=headers)
        assert purge_resp.status_code == 200
        assert purge_resp.json()["status"] == "purged"

        with SessionLocal() as db:
            record = db.get(FileObject, file_id)
            assert record is None

        download_resp = client.get(f"/files/{file_id}/download", headers=headers)
        assert download_resp.status_code == 404


def test_recycle_forbidden_for_other_user() -> None:
    with TestClient(app) as client:
        owner_token, file_id = _prepare_uploaded_file(client, email="owner.recycle@test.com", username="owner_recycle")
        owner_headers = {"Authorization": f"Bearer {owner_token}"}
        client.delete(f"/files/{file_id}", headers=owner_headers)

        client.post(
            "/auth/register",
            json={"email": "other.recycle@test.com", "username": "other_recycle", "password": "Passw0rd!"},
        )
        other_login = client.post("/auth/login", json={"account": "other_recycle", "password": "Passw0rd!"})
        other_headers = {"Authorization": f"Bearer {other_login.json()['access_token']}"}

        restore_resp = client.post(f"/recycle/files/{file_id}/restore", headers=other_headers)
        assert restore_resp.status_code == 403

        purge_resp = client.delete(f"/recycle/files/{file_id}/purge", headers=other_headers)
        assert purge_resp.status_code == 403
