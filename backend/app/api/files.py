import re
from pathlib import Path
from urllib.parse import quote

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


TEXT_PREVIEW_EXTENSIONS = {".txt", ".md", ".log", ".json", ".csv", ".yaml", ".yml"}


def _file_ext(file_name: str) -> str:
    return Path(file_name).suffix.lower()


def _is_previewable(mime_type: str, file_name: str) -> bool:
    if mime_type.startswith("image/") or mime_type == "application/pdf" or mime_type.startswith("text/"):
        return True
    return _file_ext(file_name) in TEXT_PREVIEW_EXTENSIONS


def _preview_media_type(mime_type: str, file_name: str) -> str:
    if mime_type != "application/octet-stream":
        return mime_type
    if _file_ext(file_name) in TEXT_PREVIEW_EXTENSIONS:
        return "text/plain; charset=utf-8"
    return mime_type


def _build_content_disposition(*, disposition: str, file_name: str) -> str:
    ascii_fallback = file_name.encode("ascii", "ignore").decode("ascii").strip()
    if not ascii_fallback:
        ascii_fallback = "download"
    ascii_fallback = ascii_fallback.replace("\\", "_").replace('"', "_")
    utf8_name = quote(file_name)
    return f"{disposition}; filename=\"{ascii_fallback}\"; filename*=UTF-8''{utf8_name}"


def _resolve_file_object_key(*, db: Session, file_record: FileObject) -> str:
    resolved_key = object_storage_service.resolve_object_key(
        object_key=file_record.object_key,
        file_name=file_record.file_name,
    )
    if resolved_key != file_record.object_key:
        file_record.object_key = resolved_key
        db.add(file_record)
        db.commit()
        db.refresh(file_record)
    return resolved_key


@router.get("", response_model=FileListResponse)
def get_files(
    keyword: str | None = Query(default=None),
    min_size: int | None = Query(default=None, ge=0),
    max_size: int | None = Query(default=None, ge=0),
    directory: str | None = Query(
        default=None,
        description="目录筛选，'__root__' 表示根目录直系文件，其他值表示该目录直系文件",
    ),
    sort_by: str = Query(
        default="created_at_desc",
        description="排序方式：created_at_desc/created_at_asc/file_name_asc/file_name_desc/size_desc/size_asc",
    ),
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
        directory=directory,
        sort_by=sort_by,
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

    try:
        object_key = _resolve_file_object_key(db=db, file_record=file_record)
        total_size = object_storage_service.get_file_size(object_key=object_key)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文件内容不存在") from exc

    start = 0
    end = total_size - 1
    status_code = status.HTTP_200_OK

    if range_header:
        match = re.match(r"bytes=(\d*)-(\d*)", range_header.strip())
        if not match:
            raise HTTPException(status_code=status.HTTP_416_RANGE_NOT_SATISFIABLE, detail="无效Range")

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
                raise HTTPException(status_code=status.HTTP_416_RANGE_NOT_SATISFIABLE, detail="无效Range")
            start = max(total_size - suffix, 0)
            end = total_size - 1
        else:
            raise HTTPException(status_code=status.HTTP_416_RANGE_NOT_SATISFIABLE, detail="无效Range")

        if start < 0 or end < start or start >= total_size:
            raise HTTPException(status_code=status.HTTP_416_RANGE_NOT_SATISFIABLE, detail="Range越界")
        end = min(end, total_size - 1)
        status_code = status.HTTP_206_PARTIAL_CONTENT

    try:
        data = object_storage_service.read_range(object_key=object_key, start=start, end=end)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文件内容不存在") from exc
    headers = {
        "Accept-Ranges": "bytes",
        "Content-Length": str(len(data)),
        "Content-Disposition": _build_content_disposition(
            disposition="attachment",
            file_name=file_record.file_name,
        ),
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

    if not _is_previewable(file_record.mime_type, file_record.file_name):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="当前文件类型不支持在线预览")

    try:
        object_key = _resolve_file_object_key(db=db, file_record=file_record)
        total_size = object_storage_service.get_file_size(object_key=object_key)
        data = object_storage_service.read_range(
            object_key=object_key,
            start=0,
            end=max(total_size - 1, 0),
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文件内容不存在") from exc

    headers = {
        "Content-Disposition": _build_content_disposition(
            disposition="inline",
            file_name=file_record.file_name,
        ),
        "Content-Length": str(len(data)),
    }
    return Response(
        content=data,
        media_type=_preview_media_type(file_record.mime_type, file_record.file_name),
        headers=headers,
        status_code=status.HTTP_200_OK,
    )
