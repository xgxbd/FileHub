from app.db.base import Base
from app.db.session import engine
from app.models import FileObject, User


def init_db() -> None:
    # 保证模型被导入后创建元数据。
    _ = (User, FileObject)
    Base.metadata.create_all(bind=engine)
