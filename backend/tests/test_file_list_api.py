from uuid import uuid4

from fastapi.testclient import TestClient

from app.db import SessionLocal
from app.models.file_object import FileObject
from app.models.user import User

from app.main import app


def _seed_file(owner_id: int, file_name: str, size_bytes: int) -> None:
    with SessionLocal() as db:
        db.add(
            FileObject(
                owner_id=owner_id,
                file_name=file_name,
                object_key=f"{owner_id}/{uuid4()}-{file_name}",
                size_bytes=size_bytes,
                mime_type="application/octet-stream",
                status="active",
                is_deleted=False,
            )
        )
        db.commit()


def _resolve_user_id(username: str) -> int:
    with SessionLocal() as db:
        user = db.query(User).filter(User.username == username).first()
        assert user is not None
        return user.id


def test_files_api_requires_auth() -> None:
    with TestClient(app) as client:
        response = client.get("/files")
        assert response.status_code == 401


def test_files_api_filter_and_pagination() -> None:
    with TestClient(app) as client:
        client.post(
            "/auth/register",
            json={"email": "u1@example.com", "username": "user001", "password": "Passw0rd!"},
        )
        client.post(
            "/auth/register",
            json={"email": "u2@example.com", "username": "user002", "password": "Passw0rd!"},
        )
        login = client.post("/auth/login", json={"account": "user001", "password": "Passw0rd!"})
        token = login.json()["access_token"]

        u1_id = _resolve_user_id("user001")
        u2_id = _resolve_user_id("user002")

        _seed_file(u1_id, "report-q1.pdf", 1024)
        _seed_file(u1_id, "photo.png", 4096)
        _seed_file(u2_id, "private.txt", 2048)

        base_resp = client.get("/files", headers={"Authorization": f"Bearer {token}"})
        assert base_resp.status_code == 200
        assert base_resp.json()["total"] == 2

        keyword_resp = client.get(
            "/files",
            params={"keyword": "photo"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert keyword_resp.status_code == 200
        assert keyword_resp.json()["total"] == 1
        assert keyword_resp.json()["items"][0]["file_name"] == "photo.png"

        size_resp = client.get(
            "/files",
            params={"min_size": 2000},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert size_resp.status_code == 200
        assert size_resp.json()["total"] == 1

        page_resp = client.get(
            "/files",
            params={"page": 1, "page_size": 1},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert page_resp.status_code == 200
        assert page_resp.json()["total"] == 2
        assert len(page_resp.json()["items"]) == 1
