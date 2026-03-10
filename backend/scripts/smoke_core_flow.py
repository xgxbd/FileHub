import sys
from pathlib import Path

from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.main import app


def main() -> int:
    with TestClient(app) as client:
        register = client.post(
            "/auth/register",
            json={"email": "smoke@test.com", "username": "smoke_user", "password": "Passw0rd!"},
        )
        if register.status_code not in {201, 409}:
            print(f"注册失败: {register.status_code} {register.text}")
            return 1

        login = client.post("/auth/login", json={"account": "smoke_user", "password": "Passw0rd!"})
        if login.status_code != 200:
            print(f"登录失败: {login.status_code} {login.text}")
            return 1
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        content = b"smoke-flow-content"
        chunk_size = 5
        chunks = [content[i : i + chunk_size] for i in range(0, len(content), chunk_size)]

        create = client.post(
            "/upload/sessions",
            headers=headers,
            json={
                "file_name": "smoke.txt",
                "total_size": len(content),
                "chunk_size": chunk_size,
                "total_chunks": len(chunks),
                "mime_type": "text/plain",
            },
        )
        if create.status_code != 201:
            print(f"创建上传会话失败: {create.status_code} {create.text}")
            return 1
        upload_id = create.json()["upload_id"]

        for index, part in enumerate(chunks):
            chunk_resp = client.put(
                f"/upload/sessions/{upload_id}/chunks/{index}",
                headers=headers,
                files={"chunk": ("chunk.part", part, "application/octet-stream")},
            )
            if chunk_resp.status_code != 200:
                print(f"上传分片失败[{index}]: {chunk_resp.status_code} {chunk_resp.text}")
                return 1

        done = client.post(f"/upload/sessions/{upload_id}/complete", headers=headers)
        if done.status_code != 200:
            print(f"完成上传失败: {done.status_code} {done.text}")
            return 1
        file_id = done.json()["file_id"]

        download = client.get(f"/files/{file_id}/download", headers=headers)
        if download.status_code != 200:
            print(f"下载失败: {download.status_code} {download.text}")
            return 1

        delete_resp = client.delete(f"/files/{file_id}", headers=headers)
        if delete_resp.status_code != 200:
            print(f"删除失败: {delete_resp.status_code} {delete_resp.text}")
            return 1

        recycle = client.get("/recycle/files", headers=headers)
        if recycle.status_code != 200 or recycle.json().get("total", 0) < 1:
            print(f"回收站校验失败: {recycle.status_code} {recycle.text}")
            return 1

        restore = client.post(f"/recycle/files/{file_id}/restore", headers=headers)
        if restore.status_code != 200:
            print(f"恢复失败: {restore.status_code} {restore.text}")
            return 1

        print("SMOKE_PASS: register/login/upload/download/delete/restore")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
