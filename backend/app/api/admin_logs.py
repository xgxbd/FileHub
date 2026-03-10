from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db import get_db
from app.models.operation_log import OperationLog
from app.models.user import User
from app.schemas.operation_log import OperationLogListResponse

router = APIRouter(prefix="/admin/logs", tags=["admin-logs"])


def _apply_filters(
    *,
    query: Select,
    action: str | None,
    user_id: int | None,
    start_at: datetime | None,
    end_at: datetime | None,
) -> Select:
    if action:
        query = query.where(OperationLog.action == action)
    if user_id is not None:
        query = query.where(OperationLog.user_id == user_id)
    if start_at is not None:
        query = query.where(OperationLog.created_at >= start_at)
    if end_at is not None:
        query = query.where(OperationLog.created_at <= end_at)
    return query


@router.get("", response_model=OperationLogListResponse)
def get_admin_logs(
    action: str | None = Query(default=None, min_length=1, max_length=64),
    user_id: int | None = Query(default=None, ge=1),
    start_at: datetime | None = Query(default=None),
    end_at: datetime | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OperationLogListResponse:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员可访问操作日志")

    base_query = select(OperationLog)
    filtered_query = _apply_filters(
        query=base_query,
        action=action,
        user_id=user_id,
        start_at=start_at,
        end_at=end_at,
    )
    total = db.scalar(select(func.count()).select_from(filtered_query.subquery())) or 0
    records = (
        db.execute(
            filtered_query.order_by(OperationLog.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        .scalars()
        .all()
    )
    return OperationLogListResponse(items=records, total=total, page=page, page_size=page_size)
