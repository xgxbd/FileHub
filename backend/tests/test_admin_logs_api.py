from fastapi.testclient import TestClient

from app.db import SessionLocal
from app.main import app
from app.models.user import User


def _resolve_user_id(username: str) -> int:
    with SessionLocal() as db:
        user = db.query(User).filter(User.username == username).first()
        assert user is not None
        return user.id


def _set_admin(username: str) -> None:
    with SessionLocal() as db:
        user = db.query(User).filter(User.username == username).first()
        assert user is not None
        user.role = "admin"
        db.add(user)
        db.commit()


def test_admin_logs_forbidden_for_non_admin() -> None:
    with TestClient(app) as client:
        client.post(
            "/auth/register",
            json={"email": "normal@test.com", "username": "normal001", "password": "Passw0rd!"},
        )
        login = client.post("/auth/login", json={"account": "normal001", "password": "Passw0rd!"})
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get("/admin/logs", headers=headers)
        assert response.status_code == 403


def test_admin_logs_list_filter_and_pagination() -> None:
    with TestClient(app) as client:
        client.post(
            "/auth/register",
            json={"email": "admin@test.com", "username": "admin001", "password": "Passw0rd!"},
        )
        _set_admin("admin001")
        admin_login = client.post("/auth/login", json={"account": "admin001", "password": "Passw0rd!"})
        admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

        client.post(
            "/auth/register",
            json={"email": "usera@test.com", "username": "usera001", "password": "Passw0rd!"},
        )
        client.post("/auth/login", json={"account": "usera001", "password": "Passw0rd!"})
        user_id = _resolve_user_id("usera001")

        base_resp = client.get("/admin/logs", headers=admin_headers)
        assert base_resp.status_code == 200
        base_payload = base_resp.json()
        assert base_payload["total"] >= 2
        assert len(base_payload["items"]) >= 2

        action_resp = client.get("/admin/logs", params={"action": "login"}, headers=admin_headers)
        assert action_resp.status_code == 200
        assert action_resp.json()["total"] >= 2

        user_resp = client.get("/admin/logs", params={"user_id": user_id}, headers=admin_headers)
        assert user_resp.status_code == 200
        assert user_resp.json()["total"] >= 1
        assert all(item["user_id"] == user_id for item in user_resp.json()["items"])

        page_resp = client.get("/admin/logs", params={"page": 1, "page_size": 1}, headers=admin_headers)
        assert page_resp.status_code == 200
        assert page_resp.json()["page"] == 1
        assert page_resp.json()["page_size"] == 1
        assert len(page_resp.json()["items"]) == 1
