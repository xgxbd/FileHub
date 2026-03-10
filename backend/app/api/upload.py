from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db import get_db
from app.models.file_object import FileObject
from app.models.user import User
from app.schemas.upload import (
    UploadChunkResponse,
    UploadCompleteResponse,
    UploadSessionCreateRequest,
    UploadSessionResponse,
)
from app.services.object_storage import object_storage_service
from app.services.upload_session_service import upload_session_store

router = APIRouter(prefix="/upload/sessions", tags=["upload"])


@router.post("", response_model=UploadSessionResponse, status_code=status.HTTP_201_CREATED)
def create_upload_session(payload: UploadSessionCreateRequest, current_user: User = Depends(get_current_user)):
    if payload.total_chunks != (payload.total_size + payload.chunk_size - 1) // payload.chunk_size:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="分片参数不一致")

    session = upload_session_store.create_session(
        owner_id=current_user.id,
        file_name=payload.file_name,
        total_size=payload.total_size,
        chunk_size=payload.chunk_size,
        total_chunks=payload.total_chunks,
        mime_type=payload.mime_type,
        file_hash=payload.file_hash,
    )
    return UploadSessionResponse(**session)


@router.get("/{upload_id}", response_model=UploadSessionResponse)
def get_upload_session(upload_id: str, current_user: User = Depends(get_current_user)):
    session = upload_session_store.get_session(upload_id=upload_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="上传会话不存在")

    if current_user.role != "admin" and session.get("owner_id") != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问该上传会话")

    return UploadSessionResponse(**session)


@router.put("/{upload_id}/chunks/{chunk_index}", response_model=UploadChunkResponse)
def upload_chunk(
    upload_id: str,
    chunk_index: int,
    chunk: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    session = upload_session_store.get_session(upload_id=upload_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="上传会话不存在")

    if current_user.role != "admin" and session.get("owner_id") != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权上传该会话分片")

    total_chunks = int(session["total_chunks"])
    if chunk_index < 0 or chunk_index >= total_chunks:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="分片索引越界")

    chunk_path = upload_session_store.chunk_path(upload_id=upload_id, chunk_index=chunk_index)
    chunk_path.write_bytes(chunk.file.read())

    updated_session = upload_session_store.mark_chunk_uploaded(upload_id=upload_id, chunk_index=chunk_index)
    if not updated_session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="上传会话不存在")

    return UploadChunkResponse(
        upload_id=upload_id,
        chunk_index=chunk_index,
        uploaded_count=len(updated_session.get("uploaded_chunks", [])),
    )


@router.post("/{upload_id}/complete", response_model=UploadCompleteResponse)
def complete_upload_session(
    upload_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = upload_session_store.get_session(upload_id=upload_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="上传会话不存在")

    if current_user.role != "admin" and session.get("owner_id") != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权完成该上传会话")

    total_chunks = int(session["total_chunks"])
    uploaded_chunks = set(session.get("uploaded_chunks", []))
    expected_chunks = set(range(total_chunks))
    if uploaded_chunks != expected_chunks:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="分片未全部上传")

    merged_path = upload_session_store.merged_path(upload_id=upload_id)
    with merged_path.open("wb") as merged:
        for index in range(total_chunks):
            part_path = upload_session_store.chunk_path(upload_id=upload_id, chunk_index=index)
            if not part_path.exists():
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="分片文件缺失")
            merged.write(part_path.read_bytes())

    object_key = session["object_key"]
    object_storage_service.upload_file(
        local_path=merged_path,
        object_key=object_key,
        content_type=session["mime_type"],
    )

    file_record = FileObject(
        owner_id=session["owner_id"],
        file_name=session["file_name"],
        object_key=object_key,
        size_bytes=session["total_size"],
        mime_type=session["mime_type"],
        file_hash=session.get("file_hash"),
        status="active",
        is_deleted=False,
    )
    db.add(file_record)
    db.commit()
    db.refresh(file_record)

    upload_session_store.complete_session(upload_id=upload_id, file_id=file_record.id)

    return UploadCompleteResponse(
        upload_id=upload_id,
        file_id=file_record.id,
        file_name=file_record.file_name,
        object_key=file_record.object_key,
        size_bytes=file_record.size_bytes,
    )
