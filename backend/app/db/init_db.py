from app.db.base import Base
from app.db.session import engine
from app.models import FileObject, Folder, OperationLog, User


def init_db() -> None:
    # 保证模型被导入后创建元数据。
    _ = (User, FileObject, Folder, OperationLog)
    Base.metadata.create_all(bind=engine)
