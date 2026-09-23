from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class FileOut(BaseModel):
    id: int
    original_name: str
    stored_name: str
    mimetype: str
    size: int
    encrypted: bool
    hash_sha256: Optional[str] = None
    version: int = 1
    owner_id: int
    folder_id: Optional[int] = None
    download_count: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class FileListResponse(BaseModel):
    files: list[FileOut]
    total: int


class FileMoveRequest(BaseModel):
    folder_id: Optional[int] = None


class FileVersionOut(BaseModel):
    id: int
    file_id: int
    version_number: int
    size: int
    mimetype: str
    hash_sha256: Optional[str] = None
    is_current: bool = False
    created_at: datetime
    created_by: int

    class Config:
        from_attributes = True


class FileVersionListResponse(BaseModel):
    file_id: int
    file_name: str
    current_version: int
    versions: list[FileVersionOut]