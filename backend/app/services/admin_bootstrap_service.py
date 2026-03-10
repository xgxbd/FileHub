import logging

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User
from app.services.security import get_password_hash

logger = logging.getLogger(__name__)


def ensure_admin_user(db: Session) -> str:
    if not settings.admin_bootstrap_enabled:
        return "disabled"

    email = settings.admin_email.strip().lower()
    username = settings.admin_username.strip()
    password = settings.admin_password

    user = db.execute(
        select(User).where(or_(User.email == email, User.username == username))
    ).scalar_one_or_none()

    if user is None:
        user = User(
            email=email,
            username=username,
            password_hash=get_password_hash(password),
            role="admin",
            is_active=True,
        )
        db.add(user)
        db.commit()
        logger.info("管理员账号已自动创建: %s", username)
        return "created"

    changed = False
    if user.role != "admin":
        user.role = "admin"
        changed = True
    if not user.is_active:
        user.is_active = True
        changed = True

    if changed:
        db.add(user)
        db.commit()
        logger.info("管理员账号角色已校正为 admin: %s", user.username)
        return "updated"

    logger.info("管理员账号已存在且状态正确: %s", user.username)
    return "noop"
