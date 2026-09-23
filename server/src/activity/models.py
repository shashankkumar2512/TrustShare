from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ActivityCreate(BaseModel):
    user_id: int
    action: str
    file_name: Optional[str] = None
    description: Optional[str] = None


class ActivityResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[int] = None
    resource_name: Optional[str] = None
    ip_address: Optional[str] = None
    level: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LoginSessionOut(BaseModel):
    id: int
    device_name: Optional[str] = None
    browser_name: Optional[str] = None
    device_type: Optional[str] = None
    ip_address: Optional[str] = None
    location: Optional[str] = None
    is_current: bool
    last_active: Optional[datetime] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)