from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db import get_db
from app.models.user import User
from app.schemas.folder import FolderCreateRequest, FolderItem, FolderRenameRequest, FolderTreeItem
from app.services.folder_service import create_folder, delete_folder, list_directory_paths, rename_folder
from app.services.operation_log_service import record_operation

router = APIRouter(prefix="/folders", tags=["folders"])


@router.get("/tree", response_model=list[FolderTreeItem])
def get_folder_tree(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[FolderTreeItem]:
    paths = list_directory_paths(db=db, current_user=current_user)
    return [
        FolderTreeItem(path=item.path, name=item.name, parent_path=item.parent_path)
        for item in paths
    ]


@router.post("", response_model=FolderItem, status_code=status.HTTP_201_CREATED)
def create_folder_endpoint(
    payload: FolderCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FolderItem:
    folder = create_folder(
        db=db,
        current_user=current_user,
        parent_directory=payload.parent_directory,
        folder_name=payload.folder_name,
    )
    record_operation(
        db=db,
        user=current_user,
        action="create_folder",
        target_type="folder",
        target_id=str(folder.id),
        detail={"path": folder.path},
    )
    return FolderItem.model_validate(folder)


@router.patch("/rename")
def rename_folder_endpoint(
    payload: FolderRenameRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    renamed = rename_folder(
        db=db,
        current_user=current_user,
        path=payload.path,
        new_name=payload.new_name,
    )
    record_operation(
        db=db,
        user=current_user,
        action="rename_folder",
        target_type="folder",
        target_id=renamed.path,
        detail={"path": payload.path, "new_path": renamed.path},
    )
    return {"path": renamed.path, "name": renamed.name}


@router.delete("")
def delete_folder_endpoint(
    path: str = Query(..., min_length=1),
    recursive: bool = Query(default=False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    deleted_folder = delete_folder(db=db, current_user=current_user, path=path, recursive=recursive)
    record_operation(
        db=db,
        user=current_user,
        action="delete_folder",
        target_type="folder",
        target_id=str(deleted_folder["path"]),
        detail={"path": deleted_folder["path"], "recursive": recursive},
    )
    return {**deleted_folder, "status": "deleted"}
