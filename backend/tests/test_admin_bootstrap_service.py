from sqlalchemy import select

from app.core.config import settings
from app.db import SessionLocal
from app.models.user import User
from app.services.admin_bootstrap_service import ensure_admin_user
from app.services.security import get_password_hash, verify_password


def _set_admin_settings(monkeypatch, *, email: str, username: str, password: str) -> None:
    monkeypatch.setattr(settings, "admin_bootstrap_enabled", True)
    monkeypatch.setattr(settings, "admin_email", email)
    monkeypatch.setattr(settings, "admin_username", username)
    monkeypatch.setattr(settings, "admin_password", password)


def test_admin_bootstrap_creates_admin(monkeypatch) -> None:
    _set_admin_settings(
        monkeypatch,
        email="bootstrap.create@test.com",
        username="bootstrap_create",
        password="Passw0rd!",
    )

    with SessionLocal() as db:
        result = ensure_admin_user(db)
        assert result == "created"

        user = db.execute(select(User).where(User.username == "bootstrap_create")).scalar_one()
        assert user.role == "admin"
        assert user.email == "bootstrap.create@test.com"
        assert verify_password("Passw0rd!", user.password_hash)


def test_admin_bootstrap_is_idempotent(monkeypatch) -> None:
    _set_admin_settings(
        monkeypatch,
        email="bootstrap.idempotent@test.com",
        username="bootstrap_idempotent",
        password="Passw0rd!",
    )

    with SessionLocal() as db:
        first = ensure_admin_user(db)
        second = ensure_admin_user(db)
        assert first == "created"
        assert second == "noop"


def test_admin_bootstrap_promotes_existing_user(monkeypatch) -> None:
    _set_admin_settings(
        monkeypatch,
        email="bootstrap.promote@test.com",
        username="bootstrap_promote",
        password="Passw0rd!",
    )

    with SessionLocal() as db:
        old_hash = get_password_hash("OldPassw0rd!")
        db.add(
            User(
                email="bootstrap.promote@test.com",
                username="bootstrap_promote",
                password_hash=old_hash,
                role="user",
                is_active=False,
            )
        )
        db.commit()

        result = ensure_admin_user(db)
        assert result == "updated"

        user = db.execute(select(User).where(User.username == "bootstrap_promote")).scalar_one()
        assert user.role == "admin"
        assert user.is_active is True
        assert user.password_hash == old_hash
