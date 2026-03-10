from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db import get_db
from app.models.user import User
from app.schemas.file import FileListResponse
from app.services.file_service import list_files_for_admin

router = APIRouter(prefix="/admin/files", tags=["admin-files"])


@router.get("", response_model=FileListResponse)
def get_admin_files(
    keyword: str | None = Query(default=None),
    min_size: int | None = Query(default=None, ge=0),
    max_size: int | None = Query(default=None, ge=0),
    owner_id: int | None = Query(default=None, ge=1),
    status_filter: str = Query(default="active", alias="status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FileListResponse:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员可访问文件管理")

    if status_filter not in {"active", "deleted", "all"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="status 参数仅支持 active/deleted/all")

    return list_files_for_admin(
        db=db,
        keyword=keyword,
        min_size=min_size,
        max_size=max_size,
        owner_id=owner_id,
        status_filter=status_filter,
        page=page,
        page_size=page_size,
    )
