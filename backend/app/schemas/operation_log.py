from datetime import datetime

from pydantic import BaseModel, ConfigDict


class OperationLogItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    username_snapshot: str
    action: str
    target_type: str | None
    target_id: str | None
    detail_json: str | None
    created_at: datetime


class OperationLogListResponse(BaseModel):
    items: list[OperationLogItem]
    total: int
    page: int
    page_size: int
