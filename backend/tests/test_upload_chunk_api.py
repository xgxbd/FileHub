from fastapi.testclient import TestClient

from app.main import app


def test_upload_session_requires_auth() -> None:
    with TestClient(app) as client:
        resp = client.post(
            "/upload/sessions",
            json={
                "file_name": "demo.bin",
                "total_size": 1024,
                "chunk_size": 512,
                "total_chunks": 2,
                "mime_type": "application/octet-stream",
            },
        )
        assert resp.status_code == 401


def test_upload_chunk_flow_complete() -> None:
    content = b"filehub-upload-chunk-flow"
    chunk_size = 8
    chunks = [content[i : i + chunk_size] for i in range(0, len(content), chunk_size)]

    with TestClient(app) as client:
        client.post(
            "/auth/register",
            json={"email": "chunk@test.com", "username": "chunk_tester", "password": "Passw0rd!"},
        )
        login = client.post("/auth/login", json={"account": "chunk_tester", "password": "Passw0rd!"})
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        create = client.post(
            "/upload/sessions",
            headers=headers,
            json={
                "file_name": "sample.txt",
                "total_size": len(content),
                "chunk_size": chunk_size,
                "total_chunks": len(chunks),
                "mime_type": "text/plain",
            },
        )
        assert create.status_code == 201
        upload_id = create.json()["upload_id"]

        for index, part in enumerate(chunks):
            upload_resp = client.put(
                f"/upload/sessions/{upload_id}/chunks/{index}",
                headers=headers,
                files={"chunk": ("chunk.part", part, "application/octet-stream")},
            )
            assert upload_resp.status_code == 200

        state = client.get(f"/upload/sessions/{upload_id}", headers=headers)
        assert state.status_code == 200
        assert len(state.json()["uploaded_chunks"]) == len(chunks)

        done = client.post(f"/upload/sessions/{upload_id}/complete", headers=headers)
        assert done.status_code == 200
        assert done.json()["file_name"] == "sample.txt"

        files_resp = client.get("/files", headers=headers)
        assert files_resp.status_code == 200
        assert files_resp.json()["total"] == 1
