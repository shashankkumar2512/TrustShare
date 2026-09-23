from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: str
    category: str
    title: str
    message: str
    icon: str
    is_read: bool
    resource_id: Optional[int] = None
    resource_type: Optional[str] = None
    created_at: datetime


class MarkAllReadResponse(BaseModel):
    updated: int


class DeleteAllResponse(BaseModel):
    deleted: int