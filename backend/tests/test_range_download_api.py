from fastapi.testclient import TestClient

from app.main import app


def _prepare_uploaded_file(client: TestClient, *, email: str, username: str) -> tuple[str, int, bytes]:
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
            "file_name": "range.txt",
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
