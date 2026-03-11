import bcrypt
from fastapi.testclient import TestClient

from app.db import SessionLocal
from app.models.user import User
from app.main import app


def test_auth_flow_register_login_me_refresh() -> None:
    with TestClient(app) as client:
        register_resp = client.post(
            "/auth/register",
            json={
                "email": "tester@example.com",
                "username": "tester",
                "password": "Passw0rd!",
            },
        )
        assert register_resp.status_code == 201

        login_resp = client.post(
            "/auth/login",
            json={
                "account": "tester",
                "password": "Passw0rd!",
            },
        )
        assert login_resp.status_code == 200
        tokens = login_resp.json()

        me_resp = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        assert me_resp.status_code == 200
        assert me_resp.json()["username"] == "tester"

        refresh_resp = client.post(
            "/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]},
        )
        assert refresh_resp.status_code == 200
        assert refresh_resp.json()["access_token"] != ""


def test_auth_login_with_existing_bcrypt_hash() -> None:
    password = "LegacyPassw0rd!"
    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    with SessionLocal() as db:
        db.add(
            User(
                email="legacy@example.com",
                username="legacy_user",
                password_hash=password_hash,
                role="user",
                is_active=True,
            )
        )
        db.commit()

    with TestClient(app) as client:
        login_resp = client.post(
            "/auth/login",
            json={
                "account": "legacy_user",
                "password": password,
            },
        )
        assert login_resp.status_code == 200
        assert login_resp.json()["access_token"] != ""
