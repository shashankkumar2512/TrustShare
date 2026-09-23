from sqlalchemy.orm import Session
from fastapi import HTTPException
from src.entities.folder import Folder
from src.entities.file import File
from src.entities.user import User
from src.notifications.service import create_notification
from src.security.key_manager import delete_key
from src.security.secure_storage import delete_encrypted_file
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class FolderCreate(BaseModel):
    name: str
    parent_id: Optional[int] = None

class FolderRename(BaseModel):
    name: str

class FolderOut(BaseModel):
    id: int
    name: str
    owner_id: int
    parent_id: Optional[int]
    created_at: datetime
    item_count: int = 0

    class Config:
        from_attributes = True


def list_folders(db: Session, owner_id: int, parent_id: int | None = None) -> list[FolderOut]:
    q = db.query(Folder).filter(Folder.owner_id == owner_id)
    if parent_id is not None:
        q = q.filter(Folder.parent_id == parent_id)
    else:
        q = q.filter(Folder.parent_id == None)
    folders = q.order_by(Folder.name).all()
    return [
        FolderOut(
            id=folder.id,
            name=folder.name,
            owner_id=folder.owner_id,
            parent_id=folder.parent_id,
            created_at=folder.created_at,
            item_count=(
                db.query(File)
                .filter(File.folder_id == folder.id, File.is_deleted == False)
                .count()
                + db.query(Folder).filter(Folder.parent_id == folder.id).count()
            ),
        )
        for folder in folders
    ]


def create_folder(db: Session, data: FolderCreate, owner_id: int) -> FolderOut:
    folder = Folder(name=data.name, owner_id=owner_id, parent_id=data.parent_id)
    db.add(folder)
    create_notification(
        db,
        user_id=owner_id,
        type="upload",
        category="uploads",
        title="Folder created",
        message=f'Folder "{data.name}" was created.',
        icon="folder",
    )
    db.commit()
    db.refresh(folder)
    return folder

def rename_folder(
    db: Session,
    folder_id: int,
    owner_id: int,
    new_name: str,
) -> FolderOut:
    
    if not new_name or not new_name.strip():
        raise HTTPException(status_code=400, detail="Folder name cannot be empty")

    folder = (
        db.query(Folder)
        .filter(Folder.id == folder_id, Folder.owner_id == owner_id)
        .first()
    )
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")

    folder.name = new_name.strip()
    db.commit()
    db.refresh(folder)

    return FolderOut(
        id=folder.id,
        name=folder.name,
        owner_id=folder.owner_id,
        parent_id=folder.parent_id,
        created_at=folder.created_at,
        item_count=(
            db.query(File)
            .filter(File.folder_id == folder.id, File.is_deleted == False)
            .count()
            + db.query(Folder).filter(Folder.parent_id == folder.id).count()
        ),
    )


def _folder_tree(db: Session, folder: Folder, owner_id: int) -> list[Folder]:
    folders = [folder]
    current_level = [folder.id]
    while current_level:
        children = (
            db.query(Folder)
            .filter(
                Folder.owner_id == owner_id,
                Folder.parent_id.in_(current_level),
            )
            .all()
        )
        folders.extend(children)
        current_level = [child.id for child in children]
    return folders


def delete_folder(
    db: Session,
    folder_id: int,
    owner_id: int,
    recursive: bool = False,
) -> None:
    folder = db.query(Folder).filter(Folder.id == folder_id, Folder.owner_id == owner_id).first()
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")

    folders = _folder_tree(db, folder, owner_id)
    folder_ids = [item.id for item in folders]
    files = (
        db.query(File)
        .filter(File.owner_id == owner_id, File.folder_id.in_(folder_ids))
        .all()
    )
    active_files = [file for file in files if not file.is_deleted]

    if not recursive:
        if len(folders) > 1:
            raise HTTPException(status_code=409, detail="Delete or move subfolders before deleting this folder")
        if active_files:
            raise HTTPException(status_code=409, detail="Delete or move files before deleting this folder")

    removed_size = 0
    for file in files:
        file.folder_id = None
        if file.is_deleted:
            continue
        try:
            delete_encrypted_file(file.stored_name)
        except Exception:
            pass
        if file.encrypted:
            try:
                delete_key(file.stored_name)
            except Exception:
                pass
        file.is_deleted = True
        removed_size += file.size or 0

    if removed_size:
        user = db.query(User).filter(User.id == owner_id).first()
        if user:
            user.storage_used = max(0, (user.storage_used or 0) - removed_size)

    # PostgreSQL may batch ORM deletes without preserving Python loop order.
    # Detach descendants first so the self-referencing folder FK cannot block
    # deletion of the parent in the same transaction.
    for item in folders[1:]:
        item.parent_id = None

    db.flush()
    for item in folders:
        db.delete(item)
    db.commit()
