from sqlalchemy import Select, func, select
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
) -> Select:
    if keyword:
        query = query.where(FileObject.file_name.ilike(f"%{keyword.strip()}%"))
    if min_size is not None:
        query = query.where(FileObject.size_bytes >= min_size)
    if max_size is not None:
        query = query.where(FileObject.size_bytes <= max_size)
    return query


def list_files(
    *,
    db: Session,
    current_user: User,
    deleted_only: bool = False,
    keyword: str | None,
    min_size: int | None,
    max_size: int | None,
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
    )

    count_query = select(func.count()).select_from(filtered_query.subquery())
    total = db.scalar(count_query) or 0

    list_query = filtered_query.order_by(FileObject.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    records = db.execute(list_query).scalars().all()

    return FileListResponse(
        items=records,
        total=total,
        page=page,
        page_size=page_size,
    )
