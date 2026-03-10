from datetime import datetime

from pydantic import BaseModel, ConfigDict


class FileItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int
    file_name: str
    object_key: str
    size_bytes: int
    mime_type: str
    status: str
    created_at: datetime


class FileListResponse(BaseModel):
    items: list[FileItem]
    total: int
    page: int
    page_size: int
