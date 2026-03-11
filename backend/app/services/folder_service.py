from dataclasses import dataclass

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.file_object import FileObject
from app.models.folder import Folder
from app.models.user import User


ROOT_DIRECTORY_MARKER = "__root__"


@dataclass
class FolderPathParts:
    path: str
    name: str
    parent_path: str


def normalize_directory_path(raw: str | None) -> str:
    text = str(raw or "").strip().replace("\\", "/")
    if text in {"", "/", ROOT_DIRECTORY_MARKER}:
        return ""

    parts = []
    for part in text.split("/"):
        segment = part.strip()
        if not segment:
            continue
        if segment in {".", ".."}:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="目录名不合法")
        parts.append(segment)
    return "/".join(parts)


def normalize_folder_name(raw: str) -> str:
    name = normalize_directory_path(raw)
    if not name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="文件夹名称不能为空")
    if "/" in name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="文件夹名称不能包含路径分隔符")
    return name


def split_folder_path(path: str) -> FolderPathParts:
    normalized = normalize_directory_path(path)
    if not normalized:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="根目录不能作为文件夹路径")

    parts = normalized.split("/")
    return FolderPathParts(
        path=normalized,
        name=parts[-1],
        parent_path="/".join(parts[:-1]),
    )


def _iter_parent_paths(path: str) -> list[str]:
    normalized = normalize_directory_path(path)
    if not normalized:
        return []

    parts = normalized.split("/")
    parent_paths = []
    current = ""
    for segment in parts:
        current = f"{current}/{segment}".strip("/")
        parent_paths.append(current)
    return parent_paths


def _derive_directories_from_files(file_names: list[str]) -> set[str]:
    paths: set[str] = set()
    for file_name in file_names:
        normalized = normalize_directory_path(file_name)
        if "/" not in normalized:
            continue
        segments = normalized.split("/")[:-1]
        current = ""
        for segment in segments:
            current = f"{current}/{segment}".strip("/")
            if current:
                paths.add(current)
    return paths


def list_directory_paths(*, db: Session, current_user: User) -> list[FolderPathParts]:
    explicit_folders = (
        db.execute(
            select(Folder).where(
                Folder.owner_id == current_user.id,
                Folder.is_deleted.is_(False),
            )
        )
        .scalars()
        .all()
    )
    explicit_paths = {folder.path for folder in explicit_folders}

    file_names = db.execute(
        select(FileObject.file_name).where(
            FileObject.owner_id == current_user.id,
            FileObject.is_deleted.is_(False),
        )
    ).scalars().all()
    derived_paths = _derive_directories_from_files(list(file_names))

    merged_paths = set()
    for raw_path in explicit_paths | derived_paths:
        merged_paths.update(_iter_parent_paths(raw_path))

    return [
        split_folder_path(path)
        for path in sorted(merged_paths)
    ]


def _folder_exists(*, db: Session, owner_id: int, path: str) -> bool:
    normalized = normalize_directory_path(path)
    if not normalized:
        return True

    explicit = db.execute(
        select(Folder.id).where(
            Folder.owner_id == owner_id,
            Folder.path == normalized,
            Folder.is_deleted.is_(False),
        )
    ).scalar_one_or_none()
    if explicit is not None:
        return True

    file_child = db.execute(
        select(FileObject.id).where(
            FileObject.owner_id == owner_id,
            FileObject.is_deleted.is_(False),
            FileObject.file_name.like(f"{normalized}/%"),
        )
    ).scalar_one_or_none()
    return file_child is not None


def create_folder(*, db: Session, current_user: User, parent_directory: str | None, folder_name: str) -> Folder:
    normalized_parent = normalize_directory_path(parent_directory)
    normalized_name = normalize_folder_name(folder_name)

    if normalized_parent and not _folder_exists(db=db, owner_id=current_user.id, path=normalized_parent):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="上级目录不存在")

    next_path = f"{normalized_parent}/{normalized_name}".strip("/")

    file_conflict = db.execute(
        select(FileObject.id).where(
            FileObject.owner_id == current_user.id,
            FileObject.is_deleted.is_(False),
            FileObject.file_name == next_path,
        )
    ).scalar_one_or_none()
    if file_conflict is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="同名文件已存在")

    existing_folder = db.execute(
        select(Folder).where(
            Folder.owner_id == current_user.id,
            Folder.path == next_path,
        )
    ).scalar_one_or_none()

    if existing_folder and not existing_folder.is_deleted:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="文件夹已存在")

    if existing_folder:
        existing_folder.name = normalized_name
        existing_folder.parent_path = normalized_parent
        existing_folder.is_deleted = False
        db.add(existing_folder)
        db.commit()
        db.refresh(existing_folder)
        return existing_folder

    folder = Folder(
        owner_id=current_user.id,
        path=next_path,
        name=normalized_name,
        parent_path=normalized_parent,
        is_deleted=False,
    )
    db.add(folder)
    db.commit()
    db.refresh(folder)
    return folder


def delete_folder(*, db: Session, current_user: User, path: str) -> FolderPathParts:
    target = split_folder_path(path)

    file_exists = db.execute(
        select(FileObject.id).where(
            FileObject.owner_id == current_user.id,
            FileObject.is_deleted.is_(False),
            FileObject.file_name.like(f"{target.path}/%"),
        )
    ).scalar_one_or_none()
    if file_exists is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="目录下仍有文件，不能删除")

    child_folder = db.execute(
        select(Folder.id).where(
            Folder.owner_id == current_user.id,
            Folder.is_deleted.is_(False),
            Folder.path.like(f"{target.path}/%"),
        )
    ).scalar_one_or_none()
    if child_folder is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="目录下仍有子目录，不能删除")

    folder = db.execute(
        select(Folder).where(
            Folder.owner_id == current_user.id,
            Folder.path == target.path,
            Folder.is_deleted.is_(False),
        )
    ).scalar_one_or_none()
    if folder is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文件夹不存在")

    folder.is_deleted = True
    db.add(folder)
    db.commit()
    return target
