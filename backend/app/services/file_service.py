from sqlalchemy import Select, asc, desc, func, select
from sqlalchemy.orm import Session

from app.models.file_object import FileObject
from app.models.user import User
from app.schemas.file import FileListResponse


def _apply_filters(
    *,
    query: Select,
    keyword: str | None,
    min_size: int | None,
    max_size: int | None,
    directory: str | None,
) -> Select:
    if keyword:
        query = query.where(FileObject.file_name.ilike(f"%{keyword.strip()}%"))
    if min_size is not None:
        query = query.where(FileObject.size_bytes >= min_size)
    if max_size is not None:
        query = query.where(FileObject.size_bytes <= max_size)
    if directory is not None:
        raw_directory = directory.strip()
        if raw_directory == "__root__":
            query = query.where(~FileObject.file_name.like("%/%"))
        elif raw_directory:
            normalized = raw_directory.strip("/")
            if normalized:
                prefix = f"{normalized}/"
                query = query.where(FileObject.file_name.ilike(f"{prefix}%"))
                query = query.where(~FileObject.file_name.ilike(f"{prefix}%/%"))
    return query


def _apply_sort(*, query: Select, sort_by: str) -> Select:
    sort_mapping = {
        "created_at_desc": desc(FileObject.created_at),
        "created_at_asc": asc(FileObject.created_at),
        "file_name_asc": asc(FileObject.file_name),
        "file_name_desc": desc(FileObject.file_name),
        "size_desc": desc(FileObject.size_bytes),
        "size_asc": asc(FileObject.size_bytes),
    }
    return query.order_by(sort_mapping.get(sort_by, desc(FileObject.created_at)))


def list_files(
    *,
    db: Session,
    current_user: User,
    deleted_only: bool = False,
    keyword: str | None,
    min_size: int | None,
    max_size: int | None,
    directory: str | None = None,
    sort_by: str = "created_at_desc",
    page: int,
    page_size: int,
) -> FileListResponse:
    base_query = select(FileObject).where(FileObject.is_deleted.is_(deleted_only))

    if current_user.role != "admin":
        base_query = base_query.where(FileObject.owner_id == current_user.id)

    filtered_query = _apply_filters(
        query=base_query,
        keyword=keyword,
        min_size=min_size,
        max_size=max_size,
        directory=directory,
    )

    count_query = select(func.count()).select_from(filtered_query.subquery())
    total = db.scalar(count_query) or 0

    list_query = _apply_sort(query=filtered_query, sort_by=sort_by).offset((page - 1) * page_size).limit(page_size)
    records = db.execute(list_query).scalars().all()

    return FileListResponse(
        items=records,
        total=total,
        page=page,
        page_size=page_size,
    )


def list_files_for_admin(
    *,
    db: Session,
    keyword: str | None,
    min_size: int | None,
    max_size: int | None,
    directory: str | None = None,
    owner_id: int | None,
    status_filter: str,
    sort_by: str = "created_at_desc",
    page: int,
    page_size: int,
) -> FileListResponse:
    base_query = select(FileObject)
    if status_filter == "active":
        base_query = base_query.where(FileObject.is_deleted.is_(False))
    elif status_filter == "deleted":
        base_query = base_query.where(FileObject.is_deleted.is_(True))

    if owner_id is not None:
        base_query = base_query.where(FileObject.owner_id == owner_id)

    filtered_query = _apply_filters(
        query=base_query,
        keyword=keyword,
        min_size=min_size,
        max_size=max_size,
        directory=directory,
    )
    total = db.scalar(select(func.count()).select_from(filtered_query.subquery())) or 0
    records = (
        db.execute(
            _apply_sort(query=filtered_query, sort_by=sort_by)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        .scalars()
        .all()
    )
    return FileListResponse(items=records, total=total, page=page, page_size=page_size)
