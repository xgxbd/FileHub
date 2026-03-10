from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db import get_db
from app.models.user import User
from app.schemas.file import FileListResponse
from app.services.file_service import list_files

router = APIRouter(prefix="/files", tags=["files"])


@router.get("", response_model=FileListResponse)
def get_files(
    keyword: str | None = Query(default=None),
    min_size: int | None = Query(default=None, ge=0),
    max_size: int | None = Query(default=None, ge=0),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FileListResponse:
    return list_files(
        db=db,
        current_user=current_user,
        keyword=keyword,
        min_size=min_size,
        max_size=max_size,
        page=page,
        page_size=page_size,
    )
