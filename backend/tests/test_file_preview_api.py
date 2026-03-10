from fastapi.testclient import TestClient

from app.main import app


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
