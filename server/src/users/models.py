from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    mfa_enabled: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    organization: Optional[str] = None
    avatar_url: Optional[str] = None
    mfa_enabled: Optional[bool] = None