# server/src/shared_with_me/models.py

from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, EmailStr


class SharedFileOut(BaseModel):
    permission_id: int
    file_id: int
    name: str
    mimetype: str
    size: int
    encrypted: bool
    permission: str
    shared_by: str
    shared_by_email: str
    shared_at: datetime
    updated_at: Optional[datetime] = None
    can_download: bool
    access_count: int = 0
    last_accessed_at: Optional[datetime] = None


class SharedFilesResponse(BaseModel):
    files: list[SharedFileOut]
    total: int
    view_only: int
    downloadable: int


class DirectShareCreate(BaseModel):
    file_id: int
    recipient_email: EmailStr
    permission: Literal["view", "download"] = "view"


class DirectShareUpdateRequest(BaseModel):
    permission: Literal["view", "download"] = "view"


class DirectShareOut(BaseModel):
    permission_id: int
    file_id: int
    file_name: str
    recipient_id: int
    recipient_name: str
    recipient_email: str
    permission: str
    access_count: int = 0
    last_accessed_at: Optional[datetime] = None
    shared_at: datetime


class DirectSharesResponse(BaseModel):
    shares: list[DirectShareOut]
    total: int