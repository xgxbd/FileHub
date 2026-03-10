import sys
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import or_, select

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.core.config import settings
from app.db import SessionLocal
from app.main import app
from app.models.user import User


def main() -> None:
    with TestClient(app):
        pass

    with SessionLocal() as db:
        user = db.execute(
            select(User).where(
                or_(
                    User.email == settings.admin_email.strip().lower(),
                    User.username == settings.admin_username.strip(),
                )
            )
        ).scalar_one_or_none()

    print(f"bootstrap_enabled={settings.admin_bootstrap_enabled}")
    if user is None:
        print("admin_user_found=false")
        return

    print("admin_user_found=true")
    print(f"admin_username={user.username}")
    print(f"admin_email={user.email}")
    print(f"admin_role={user.role}")
    print(f"admin_active={user.is_active}")


if __name__ == "__main__":
    main()
