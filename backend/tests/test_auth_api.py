from fastapi.testclient import TestClient

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
