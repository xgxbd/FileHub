from fastapi.testclient import TestClient

from app.db import SessionLocal
from app.main import app
from app.models.user import User


def _set_admin(username: str) -> None:
    with SessionLocal() as db:
        user = db.query(User).filter(User.username == username).first()
        assert user is not None
        user.role = "admin"
        db.add(user)
        db.commit()


def _upload_demo_file(client: TestClient, *, token: str, file_name: str, content: bytes) -> int:
    headers = {"Authorization": f"Bearer {token}"}
    chunk_size = 4
    chunks = [content[i : i + chunk_size] for i in range(0, len(content), chunk_size)]

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
            files={"chunk": ("part.bin", part, "application/octet-stream")},
        )
    done = client.post(f"/upload/sessions/{upload_id}/complete", headers=headers)
    return done.json()["file_id"]


def test_admin_files_forbidden_for_non_admin() -> None:
    with TestClient(app) as client:
        client.post(
            "/auth/register",
            json={"email": "normal.files@test.com", "username": "normal_files", "password": "Passw0rd!"},
        )
        login = client.post("/auth/login", json={"account": "normal_files", "password": "Passw0rd!"})
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        response = client.get("/admin/files", headers=headers)
        assert response.status_code == 403


def test_admin_files_filter_and_pagination() -> None:
    with TestClient(app) as client:
        client.post(
            "/auth/register",
            json={"email": "admin.files@test.com", "username": "admin_files", "password": "Passw0rd!"},
        )
        _set_admin("admin_files")
        admin_login = client.post("/auth/login", json={"account": "admin_files", "password": "Passw0rd!"})
        admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

        client.post(
            "/auth/register",
            json={"email": "user.files@test.com", "username": "user_files", "password": "Passw0rd!"},
        )
        user_login = client.post("/auth/login", json={"account": "user_files", "password": "Passw0rd!"})
        user_token = user_login.json()["access_token"]
        user_headers = {"Authorization": f"Bearer {user_token}"}

        file_id = _upload_demo_file(client, token=user_token, file_name="report.txt", content=b"admin-file-check")

        base_resp = client.get("/admin/files", headers=admin_headers)
        assert base_resp.status_code == 200
        assert base_resp.json()["total"] >= 1

        owner_id = base_resp.json()["items"][0]["owner_id"]
        owner_resp = client.get("/admin/files", params={"owner_id": owner_id}, headers=admin_headers)
        assert owner_resp.status_code == 200
        assert owner_resp.json()["total"] >= 1
        assert all(item["owner_id"] == owner_id for item in owner_resp.json()["items"])

        keyword_resp = client.get("/admin/files", params={"keyword": "report"}, headers=admin_headers)
        assert keyword_resp.status_code == 200
        assert keyword_resp.json()["total"] >= 1

        client.delete(f"/files/{file_id}", headers=user_headers)
        deleted_resp = client.get("/admin/files", params={"status": "deleted"}, headers=admin_headers)
        assert deleted_resp.status_code == 200
        assert deleted_resp.json()["total"] >= 1
        assert all(item["status"] == "deleted" for item in deleted_resp.json()["items"])

        page_resp = client.get(
            "/admin/files",
            params={"status": "deleted", "page": 1, "page_size": 1},
            headers=admin_headers,
        )
        assert page_resp.status_code == 200
        assert page_resp.json()["page_size"] == 1
        assert len(page_resp.json()["items"]) == 1

        invalid_status = client.get("/admin/files", params={"status": "archived"}, headers=admin_headers)
        assert invalid_status.status_code == 400
