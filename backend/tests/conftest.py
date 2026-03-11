import os
import shutil
import sys
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

os.environ["DATABASE_URL"] = "sqlite:///./test_suite.db"
os.environ["APP_SERVE_FRONTEND"] = "false"
os.environ["ADMIN_BOOTSTRAP_ENABLED"] = "false"

from app.db import Base, engine
from app.models import FileObject, Folder, OperationLog, User
from app.core.config import settings


@pytest.fixture(autouse=True)
def reset_test_database():
    _ = (User, FileObject, Folder, OperationLog)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    tmp_upload_dir = Path(settings.upload_tmp_dir)
    tmp_object_dir = tmp_upload_dir.resolve().parent / "object_store"
    if tmp_upload_dir.exists():
        shutil.rmtree(tmp_upload_dir)
    if tmp_object_dir.exists():
        shutil.rmtree(tmp_object_dir)
    yield
