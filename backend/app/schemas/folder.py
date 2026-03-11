from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class FolderItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int
    path: str
    name: str
    parent_path: str
    is_deleted: bool
    created_at: datetime
    updated_at: datetime


class FolderTreeItem(BaseModel):
    path: str
    name: str
    parent_path: str


class FolderCreateRequest(BaseModel):
    parent_directory: str | None = Field(default=None, max_length=255)
    folder_name: str = Field(min_length=1, max_length=128)
