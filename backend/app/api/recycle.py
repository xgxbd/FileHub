from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db import get_db
from app.models.file_object import FileObject
from app.models.user import User
from app.schemas.file import FileListResponse
from app.services.file_service import list_files
from app.services.object_storage import object_storage_service
from app.services.operation_log_service import record_operation

router = APIRouter(prefix="/recycle", tags=["recycle"])


@router.get("/files", response_model=FileListResponse)
def get_recycle_files(
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
        deleted_only=True,
        keyword=keyword,
        min_size=min_size,
        max_size=max_size,
        page=page,
        page_size=page_size,
    )


@router.post("/files/{file_id}/restore")
def restore_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    file_record = db.get(FileObject, file_id)
    if not file_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文件不存在")
    if not file_record.is_deleted:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="文件不在回收站")
    if current_user.role != "admin" and file_record.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权恢复该文件")

    file_record.is_deleted = False
    file_record.status = "active"
    db.add(file_record)
    db.commit()

    record_operation(
        db=db,
        user=current_user,
        action="restore",
        target_type="file",
        target_id=str(file_record.id),
        detail={"file_name": file_record.file_name},
    )

    return {"file_id": file_record.id, "status": file_record.status}


@router.delete("/files/{file_id}/purge")
def purge_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    file_record = db.get(FileObject, file_id)
    if not file_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文件不存在")
    if not file_record.is_deleted:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="文件不在回收站")
    if current_user.role != "admin" and file_record.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权彻底删除该文件")

    object_storage_service.delete_object(object_key=file_record.object_key)
    file_name = file_record.file_name
    db.delete(file_record)
    db.commit()

    record_operation(
        db=db,
        user=current_user,
        action="purge",
        target_type="file",
        target_id=str(file_id),
        detail={"file_name": file_name},
    )

    return {"file_id": file_id, "status": "purged"}
