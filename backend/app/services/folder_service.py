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


def list_deleted_folders(*, db: Session, current_user: User) -> list[Folder]:
    return (
        db.execute(
            select(Folder).where(
                Folder.owner_id == current_user.id,
                Folder.is_deleted.is_(True),
            ).order_by(Folder.updated_at.desc(), Folder.path.asc())
        )
        .scalars()
        .all()
    )


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


def _folder_exists_with_deleted(*, db: Session, owner_id: int, path: str) -> bool:
    normalized = normalize_directory_path(path)
    if not normalized:
        return True

    explicit = db.execute(
        select(Folder.id).where(
            Folder.owner_id == owner_id,
            Folder.path == normalized,
        )
    ).scalar_one_or_none()
    if explicit is not None:
        return True

    file_record = db.execute(
        select(FileObject.id).where(
            FileObject.owner_id == owner_id,
            FileObject.file_name.like(f"{normalized}/%"),
        )
    ).scalar_one_or_none()
    return file_record is not None


def _collect_file_records(*, db: Session, owner_id: int, prefix: str, deleted: bool | None) -> list[FileObject]:
    query = select(FileObject).where(
        FileObject.owner_id == owner_id,
        FileObject.file_name.like(f"{prefix}/%"),
    )
    if deleted is not None:
        query = query.where(FileObject.is_deleted.is_(deleted))
    return db.execute(query.order_by(FileObject.file_name.asc())).scalars().all()


def _collect_explicit_folders(*, db: Session, owner_id: int, prefix: str, deleted: bool | None) -> list[Folder]:
    query = select(Folder).where(
        Folder.owner_id == owner_id,
        ((Folder.path == prefix) | Folder.path.like(f"{prefix}/%")),
    )
    if deleted is not None:
        query = query.where(Folder.is_deleted.is_(deleted))
    return db.execute(query.order_by(Folder.path.asc())).scalars().all()


def _collect_derived_paths_from_records(file_records: list[FileObject], *, prefix: str) -> set[str]:
    file_paths = [record.file_name for record in file_records]
    return {
        path
        for path in _derive_directories_from_files(file_paths)
        if path == prefix or path.startswith(f"{prefix}/")
    }


def _upsert_folder_rows(*, db: Session, owner_id: int, paths: set[str], is_deleted: bool) -> list[Folder]:
    updated_rows: list[Folder] = []
    for path in sorted(paths):
        parts = split_folder_path(path)
        row = db.execute(
            select(Folder).where(
                Folder.owner_id == owner_id,
                Folder.path == parts.path,
            )
        ).scalar_one_or_none()
        if row is None:
            row = Folder(
                owner_id=owner_id,
                path=parts.path,
                name=parts.name,
                parent_path=parts.parent_path,
                is_deleted=is_deleted,
            )
        else:
            row.name = parts.name
            row.parent_path = parts.parent_path
            row.is_deleted = is_deleted
        db.add(row)
        updated_rows.append(row)
    return updated_rows


def _rename_path(path: str, *, source_prefix: str, target_prefix: str) -> str:
    if path == source_prefix:
        return target_prefix
    if path.startswith(f"{source_prefix}/"):
        return f"{target_prefix}{path[len(source_prefix):]}"
    return path


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


def rename_folder(*, db: Session, current_user: User, path: str, new_name: str) -> FolderPathParts:
    target = split_folder_path(path)
    normalized_name = normalize_folder_name(new_name)
    destination_path = f"{target.parent_path}/{normalized_name}".strip("/")

    if destination_path == target.path:
        return split_folder_path(destination_path)

    if not _folder_exists(db=db, owner_id=current_user.id, path=target.path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文件夹不存在")

    destination_file_conflict = db.execute(
        select(FileObject.id).where(
            FileObject.owner_id == current_user.id,
            FileObject.is_deleted.is_(False),
            ((FileObject.file_name == destination_path) | FileObject.file_name.like(f"{destination_path}/%")),
        )
    ).scalar_one_or_none()
    if destination_file_conflict is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="目标名称已存在")

    destination_folder_conflict = db.execute(
        select(Folder.id).where(
            Folder.owner_id == current_user.id,
            Folder.path == destination_path,
        )
    ).scalar_one_or_none()
    if destination_folder_conflict is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="目标名称已存在")

    folder_rows = _collect_explicit_folders(
        db=db,
        owner_id=current_user.id,
        prefix=target.path,
        deleted=False,
    )
    for folder in folder_rows:
        new_path = _rename_path(folder.path, source_prefix=target.path, target_prefix=destination_path)
        new_parts = split_folder_path(new_path)
        folder.path = new_parts.path
        folder.name = new_parts.name
        folder.parent_path = new_parts.parent_path
        db.add(folder)

    file_rows = _collect_file_records(
        db=db,
        owner_id=current_user.id,
        prefix=target.path,
        deleted=None,
    )
    for file_record in file_rows:
        file_record.file_name = _rename_path(file_record.file_name, source_prefix=target.path, target_prefix=destination_path)
        db.add(file_record)

    db.commit()
    return split_folder_path(destination_path)


def delete_folder(*, db: Session, current_user: User, path: str, recursive: bool = False) -> dict[str, int | str]:
    target = split_folder_path(path)

    if not _folder_exists(db=db, owner_id=current_user.id, path=target.path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文件夹不存在")

    active_file_records = _collect_file_records(
        db=db,
        owner_id=current_user.id,
        prefix=target.path,
        deleted=False,
    )
    active_folder_rows = _collect_explicit_folders(
        db=db,
        owner_id=current_user.id,
        prefix=target.path,
        deleted=False,
    )
    active_derived_paths = _collect_derived_paths_from_records(active_file_records, prefix=target.path)

    if not recursive:
        if active_file_records:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="目录下仍有文件，不能删除")

        child_folder = any(folder.path != target.path for folder in active_folder_rows) or any(
            path_item != target.path for path_item in active_derived_paths
        )
        if child_folder:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="目录下仍有子目录，不能删除")

    folder = db.execute(
        select(Folder).where(
            Folder.owner_id == current_user.id,
            Folder.path == target.path,
            Folder.is_deleted.is_(False),
        )
    ).scalar_one_or_none()

    affected_paths = {target.path, *active_derived_paths}
    affected_paths.update(folder_item.path for folder_item in active_folder_rows)
    _upsert_folder_rows(db=db, owner_id=current_user.id, paths=affected_paths, is_deleted=True)

    for file_record in active_file_records:
        file_record.is_deleted = True
        file_record.status = "deleted"
        db.add(file_record)

    if folder is not None:
        folder.is_deleted = True
        db.add(folder)

    db.commit()
    return {
        "path": target.path,
        "file_count": len(active_file_records),
        "folder_count": len(affected_paths),
    }


def restore_folder(*, db: Session, current_user: User, path: str) -> dict[str, int | str]:
    target = split_folder_path(path)

    folder = db.execute(
        select(Folder).where(
            Folder.owner_id == current_user.id,
            Folder.path == target.path,
            Folder.is_deleted.is_(True),
        )
    ).scalar_one_or_none()
    if folder is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文件夹不在回收站")

    if _folder_exists(db=db, owner_id=current_user.id, path=target.path):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="存在同名活跃目录，无法恢复")

    deleted_file_records = _collect_file_records(
        db=db,
        owner_id=current_user.id,
        prefix=target.path,
        deleted=True,
    )
    deleted_folder_rows = _collect_explicit_folders(
        db=db,
        owner_id=current_user.id,
        prefix=target.path,
        deleted=True,
    )

    for ancestor_path in _iter_parent_paths(target.path)[:-1]:
        _upsert_folder_rows(db=db, owner_id=current_user.id, paths={ancestor_path}, is_deleted=False)

    for folder_row in deleted_folder_rows:
        folder_row.is_deleted = False
        db.add(folder_row)

    for file_record in deleted_file_records:
        file_record.is_deleted = False
        file_record.status = "active"
        db.add(file_record)

    db.commit()
    return {
        "path": target.path,
        "file_count": len(deleted_file_records),
        "folder_count": len(deleted_folder_rows),
    }


def purge_folder(*, db: Session, current_user: User, path: str) -> dict[str, int | str]:
    target = split_folder_path(path)

    folder = db.execute(
        select(Folder).where(
            Folder.owner_id == current_user.id,
            Folder.path == target.path,
            Folder.is_deleted.is_(True),
        )
    ).scalar_one_or_none()
    if folder is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文件夹不在回收站")

    deleted_file_records = _collect_file_records(
        db=db,
        owner_id=current_user.id,
        prefix=target.path,
        deleted=True,
    )
    deleted_folder_rows = _collect_explicit_folders(
        db=db,
        owner_id=current_user.id,
        prefix=target.path,
        deleted=True,
    )

    for file_record in deleted_file_records:
        db.delete(file_record)

    for folder_row in deleted_folder_rows:
        db.delete(folder_row)

    db.commit()
    return {
        "path": target.path,
        "file_count": len(deleted_file_records),
        "folder_count": len(deleted_folder_rows),
    }
