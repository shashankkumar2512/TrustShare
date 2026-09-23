from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from src.database.core import get_db
from src.auth.dependencies import get_current_user
from src.entities.user import User
from src.folders.service import (
    FolderCreate,
    FolderOut,
    FolderRename,
    list_folders,
    create_folder,
    delete_folder,
    rename_folder,
)

router = APIRouter()


@router.get("/", response_model=list[FolderOut])
def get_folders(
    parent_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_folders(db, current_user.id, parent_id)


@router.post("/", response_model=FolderOut, status_code=201)
def create(data: FolderCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return create_folder(db, data, current_user.id)


@router.patch("/{folder_id}", response_model=FolderOut)
def rename(
    folder_id: int,
    data: FolderRename,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return rename_folder(db, folder_id, current_user.id, data.name)


@router.delete("/{folder_id}", status_code=204)
def delete(
    folder_id: int,
    recursive: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    delete_folder(db, folder_id, current_user.id, recursive=recursive)