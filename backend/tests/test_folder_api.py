from fastapi.testclient import TestClient

from app.db import SessionLocal
from app.models.file_object import FileObject
from app.models.user import User

from app.main import app


def _resolve_user_id(username: str) -> int:
    with SessionLocal() as db:
        user = db.query(User).filter(User.username == username).first()
        assert user is not None
        return user.id


def _seed_file(owner_id: int, file_name: str) -> None:
    with SessionLocal() as db:
        db.add(
            FileObject(
                owner_id=owner_id,
                file_name=file_name,
                object_key=f"{owner_id}/{file_name}",
                size_bytes=32,
                mime_type="text/plain",
                status="active",
                is_deleted=False,
            )
        )
        db.commit()


def test_folder_tree_merges_explicit_and_file_derived_directories() -> None:
    with TestClient(app) as client:
        client.post(
            "/auth/register",
            json={"email": "foldertree@example.com", "username": "foldertree", "password": "Passw0rd!"},
        )
        login = client.post("/auth/login", json={"account": "foldertree", "password": "Passw0rd!"})
        token = login.json()["access_token"]
        user_id = _resolve_user_id("foldertree")

        _seed_file(user_id, "logs/runtime/app.log")
        create_resp = client.post(
            "/folders",
            headers={"Authorization": f"Bearer {token}"},
            json={"parent_directory": "logs", "folder_name": "archive"},
        )
        assert create_resp.status_code == 201

        tree_resp = client.get("/folders/tree", headers={"Authorization": f"Bearer {token}"})
        assert tree_resp.status_code == 200
        assert tree_resp.json() == [
            {"path": "logs", "name": "logs", "parent_path": ""},
            {"path": "logs/archive", "name": "archive", "parent_path": "logs"},
            {"path": "logs/runtime", "name": "runtime", "parent_path": "logs"},
        ]


def test_create_and_delete_empty_folder() -> None:
    with TestClient(app) as client:
        client.post(
            "/auth/register",
            json={"email": "foldercreate@example.com", "username": "foldercreate", "password": "Passw0rd!"},
        )
        login = client.post("/auth/login", json={"account": "foldercreate", "password": "Passw0rd!"})
        token = login.json()["access_token"]

        root_create = client.post(
            "/folders",
            headers={"Authorization": f"Bearer {token}"},
            json={"parent_directory": "__root__", "folder_name": "logs"},
        )
        assert root_create.status_code == 201
        assert root_create.json()["path"] == "logs"

        child_create = client.post(
            "/folders",
            headers={"Authorization": f"Bearer {token}"},
            json={"parent_directory": "logs", "folder_name": "archive"},
        )
        assert child_create.status_code == 201
        assert child_create.json()["path"] == "logs/archive"

        delete_child = client.delete(
            "/folders",
            params={"path": "logs/archive"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert delete_child.status_code == 200
        assert delete_child.json()["path"] == "logs/archive"


def test_create_folder_conflicts_with_same_level_name() -> None:
    with TestClient(app) as client:
        client.post(
            "/auth/register",
            json={"email": "folderdup@example.com", "username": "folderdup", "password": "Passw0rd!"},
        )
        login = client.post("/auth/login", json={"account": "folderdup", "password": "Passw0rd!"})
        token = login.json()["access_token"]

        first = client.post(
            "/folders",
            headers={"Authorization": f"Bearer {token}"},
            json={"parent_directory": "__root__", "folder_name": "logs"},
        )
        assert first.status_code == 201

        duplicate = client.post(
            "/folders",
            headers={"Authorization": f"Bearer {token}"},
            json={"parent_directory": "/", "folder_name": "logs"},
        )
        assert duplicate.status_code == 409


def test_delete_folder_rejects_non_empty_directory() -> None:
    with TestClient(app) as client:
        client.post(
            "/auth/register",
            json={"email": "foldernonempty@example.com", "username": "foldernonempty", "password": "Passw0rd!"},
        )
        login = client.post("/auth/login", json={"account": "foldernonempty", "password": "Passw0rd!"})
        token = login.json()["access_token"]
        user_id = _resolve_user_id("foldernonempty")

        _seed_file(user_id, "logs/readme.txt")
        resp = client.delete(
            "/folders",
            params={"path": "logs"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 400
        assert resp.json()["detail"] == "目录下仍有文件，不能删除"


def test_delete_folder_rejects_directory_with_child_folder() -> None:
    with TestClient(app) as client:
        client.post(
            "/auth/register",
            json={"email": "folderchild@example.com", "username": "folderchild", "password": "Passw0rd!"},
        )
        login = client.post("/auth/login", json={"account": "folderchild", "password": "Passw0rd!"})
        token = login.json()["access_token"]

        client.post(
            "/folders",
            headers={"Authorization": f"Bearer {token}"},
            json={"parent_directory": "__root__", "folder_name": "logs"},
        )
        client.post(
            "/folders",
            headers={"Authorization": f"Bearer {token}"},
            json={"parent_directory": "logs", "folder_name": "archive"},
        )

        resp = client.delete(
            "/folders",
            params={"path": "logs"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 400
        assert resp.json()["detail"] == "目录下仍有子目录，不能删除"
