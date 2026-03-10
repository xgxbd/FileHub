import re

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db import get_db
from app.models.file_object import FileObject
from app.models.user import User
from app.schemas.file import FileListResponse
from app.services.file_service import list_files
from app.services.object_storage import object_storage_service
from app.services.operation_log_service import record_operation

router = APIRouter(prefix="/files", tags=["files"])


def _is_previewable(mime_type: str) -> bool:
    return mime_type.startswith("image/") or mime_type == "application/pdf" or mime_type.startswith("text/")


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
        deleted_only=False,
        keyword=keyword,
        min_size=min_size,
        max_size=max_size,
        page=page,
        page_size=page_size,
    )


@router.delete("/{file_id}")
def soft_delete_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    file_record = db.get(FileObject, file_id)
    if not file_record or file_record.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文件不存在")

    if current_user.role != "admin" and file_record.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权删除该文件")

    file_record.is_deleted = True
    file_record.status = "deleted"
    db.add(file_record)
    db.commit()

    record_operation(
        db=db,
        user=current_user,
        action="soft_delete",
        target_type="file",
        target_id=str(file_record.id),
        detail={"file_name": file_record.file_name},
    )

    return {"file_id": file_record.id, "status": file_record.status}


@router.get("/{file_id}/download")
def download_file(
    file_id: int,
    range_header: str | None = Header(default=None, alias="Range"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    file_record = db.get(FileObject, file_id)
    if not file_record or file_record.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文件不存在")

    if current_user.role != "admin" and file_record.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权下载该文件")

    total_size = object_storage_service.get_file_size(object_key=file_record.object_key)
    start = 0
    end = total_size - 1
    status_code = status.HTTP_200_OK

    if range_header:
        match = re.match(r"bytes=(\d*)-(\d*)", range_header.strip())
        if not match:
            raise HTTPException(status_code=status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE, detail="无效Range")

        start_group, end_group = match.groups()
        if start_group and end_group:
            start = int(start_group)
            end = int(end_group)
        elif start_group:
            start = int(start_group)
            end = total_size - 1
        elif end_group:
            suffix = int(end_group)
            if suffix <= 0:
                raise HTTPException(status_code=status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE, detail="无效Range")
            start = max(total_size - suffix, 0)
            end = total_size - 1
        else:
            raise HTTPException(status_code=status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE, detail="无效Range")

        if start < 0 or end < start or start >= total_size:
            raise HTTPException(status_code=status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE, detail="Range越界")
        end = min(end, total_size - 1)
        status_code = status.HTTP_206_PARTIAL_CONTENT

    data = object_storage_service.read_range(object_key=file_record.object_key, start=start, end=end)
    headers = {
        "Accept-Ranges": "bytes",
        "Content-Length": str(len(data)),
        "Content-Disposition": f'attachment; filename=\"{file_record.file_name}\"',
    }
    if status_code == status.HTTP_206_PARTIAL_CONTENT:
        headers["Content-Range"] = f"bytes {start}-{end}/{total_size}"

    record_operation(
        db=db,
        user=current_user,
        action="download",
        target_type="file",
        target_id=str(file_record.id),
        detail={
            "file_name": file_record.file_name,
            "range": range_header or "bytes=0-",
        },
    )

    return Response(content=data, media_type=file_record.mime_type, status_code=status_code, headers=headers)


@router.get("/{file_id}/preview")
def preview_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    file_record = db.get(FileObject, file_id)
    if not file_record or file_record.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文件不存在")

    if current_user.role != "admin" and file_record.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权预览该文件")

    if not _is_previewable(file_record.mime_type):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="当前文件类型不支持在线预览")

    total_size = object_storage_service.get_file_size(object_key=file_record.object_key)
    data = object_storage_service.read_range(
        object_key=file_record.object_key,
        start=0,
        end=max(total_size - 1, 0),
    )

    headers = {
        "Content-Disposition": f'inline; filename=\"{file_record.file_name}\"',
        "Content-Length": str(len(data)),
    }
    return Response(content=data, media_type=file_record.mime_type, headers=headers, status_code=status.HTTP_200_OK)
