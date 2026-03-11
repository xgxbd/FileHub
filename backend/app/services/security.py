from datetime import datetime, timedelta, timezone
from uuid import uuid4

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings


def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _build_token(
    *,
    user_id: int,
    role: str,
    token_type: str,
    expires_delta: timedelta,
    jti: str | None = None,
) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "role": role,
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
        "jti": jti or str(uuid4()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_access_token(*, user_id: int, role: str) -> str:
    expires = timedelta(minutes=settings.jwt_access_expire_minutes)
    return _build_token(user_id=user_id, role=role, token_type="access", expires_delta=expires)


def create_refresh_token(*, user_id: int, role: str) -> tuple[str, str]:
    expires = timedelta(days=settings.jwt_refresh_expire_days)
    jti = str(uuid4())
    token = _build_token(user_id=user_id, role=role, token_type="refresh", expires_delta=expires, jti=jti)
    return token, jti


def decode_token(token: str, *, expected_type: str | None = None) -> dict:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise ValueError("无效的令牌") from exc

    token_type = payload.get("type")
    if expected_type and token_type != expected_type:
        raise ValueError("令牌类型不匹配")

    return payload
