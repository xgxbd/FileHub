import json
import logging
from typing import Any

from sqlalchemy.orm import Session

from app.models.operation_log import OperationLog
from app.models.user import User

logger = logging.getLogger(__name__)


def record_operation(
    *,
    db: Session,
    user: User,
    action: str,
    target_type: str | None = None,
    target_id: str | None = None,
    detail: dict[str, Any] | None = None,
) -> None:
    detail_json = None
    if detail is not None:
        detail_json = json.dumps(detail, ensure_ascii=False)

    log_item = OperationLog(
        user_id=user.id,
        username_snapshot=user.username,
        action=action,
        target_type=target_type,
        target_id=target_id,
        detail_json=detail_json,
    )
    try:
        db.add(log_item)
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("写入操作日志失败")
