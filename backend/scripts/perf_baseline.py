import statistics
import sys
import time
from pathlib import Path

from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.main import app


def _measure_ms(fn, rounds: int) -> list[float]:
    values = []
    for _ in range(rounds):
        start = time.perf_counter()
        fn()
        values.append((time.perf_counter() - start) * 1000)
    return values


def _upload_one_file(client: TestClient, headers: dict[str, str], file_name: str, content: bytes) -> int:
    chunk_size = 8
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
    create.raise_for_status()
    upload_id = create.json()["upload_id"]

    for index, part in enumerate(chunks):
        chunk_resp = client.put(
            f"/upload/sessions/{upload_id}/chunks/{index}",
            headers=headers,
            files={"chunk": ("chunk.part", part, "application/octet-stream")},
        )
        chunk_resp.raise_for_status()

    done = client.post(f"/upload/sessions/{upload_id}/complete", headers=headers)
    done.raise_for_status()
    return done.json()["file_id"]


def main() -> int:
    with TestClient(app) as client:
        client.post(
            "/auth/register",
            json={"email": "perf@test.com", "username": "perf_user", "password": "Passw0rd!"},
        )
        login = client.post("/auth/login", json={"account": "perf_user", "password": "Passw0rd!"})
        if login.status_code != 200:
            print(f"登录失败: {login.status_code} {login.text}")
            return 1

        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        seed_file_id = _upload_one_file(client, headers, "perf-seed.txt", b"seed-content-for-download")

        list_values = _measure_ms(lambda: client.get("/files", headers=headers).raise_for_status(), rounds=20)
        download_values = _measure_ms(
            lambda: client.get(f"/files/{seed_file_id}/download", headers=headers).raise_for_status(),
            rounds=20,
        )
        upload_values = _measure_ms(
            lambda: _upload_one_file(client, headers, f"perf-{time.time_ns()}.txt", b"x" * 64),
            rounds=10,
        )

    print("PERF_BASELINE(ms)")
    print(f"files_list_avg={statistics.mean(list_values):.2f}")
    print(f"files_download_avg={statistics.mean(download_values):.2f}")
    print(f"upload_complete_avg={statistics.mean(upload_values):.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
