from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.upload import UploadSessionCreateRequest, UploadSessionResponse
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
