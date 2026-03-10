from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.user import User
from app.services.refresh_session import RefreshSessionStore, refresh_token_ttl_seconds
from app.services.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)

refresh_store = RefreshSessionStore()


def register_user(*, db: Session, email: str, username: str, password: str) -> User:
    existing = db.execute(
        select(User).where(or_(User.email == email, User.username == username))
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="邮箱或用户名已存在")

    user = User(
        email=email.strip().lower(),
        username=username.strip(),
        password_hash=get_password_hash(password),
        role="user",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(*, db: Session, account: str, password: str) -> User:
    user = db.execute(
        select(User).where(or_(User.email == account.strip().lower(), User.username == account.strip()))
    ).scalar_one_or_none()

    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="账号或密码错误")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号已禁用")

    return user


def issue_tokens(*, user: User) -> dict:
    access_token = create_access_token(user_id=user.id, role=user.role)
    refresh_token, jti = create_refresh_token(user_id=user.id, role=user.role)
    refresh_store.save(jti=jti, user_id=user.id, ttl_seconds=refresh_token_ttl_seconds())
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": 60 * 30,
    }


def refresh_user_tokens(*, db: Session, refresh_token: str) -> dict:
    payload = decode_token(refresh_token, expected_type="refresh")
    user_id = int(payload.get("sub", "0"))
    jti = payload.get("jti")
    if not user_id or not jti:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="刷新令牌无效")

    if not refresh_store.exists(jti=jti):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="刷新令牌已失效")

    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户状态无效")

    refresh_store.revoke(jti=jti)
    return issue_tokens(user=user)
