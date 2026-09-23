from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


ACTIVITIES = (
    "file_shares",
    "downloads",
    "security_alerts",
    "link_expirations",
    "access_changes",
    "system_updates",
)


class ProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    email: EmailStr
    organization: Optional[str] = None
    avatar_url: Optional[str] = None


class ProfileUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    organization: Optional[str] = Field(default=None, max_length=200)
    avatar_url: Optional[str] = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)


class SessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    device_name: Optional[str]
    browser_name: Optional[str]
    device_type: Optional[str]
    ip_address: Optional[str]
    location: Optional[str]
    last_active: Optional[str]
    is_current: bool


class ChannelPreference(BaseModel):
    in_app: bool
    email: bool


class NotificationPreferences(BaseModel):
    file_shares: ChannelPreference
    downloads: ChannelPreference
    security_alerts: ChannelPreference
    link_expirations: ChannelPreference
    access_changes: ChannelPreference
    system_updates: ChannelPreference
    digest_frequency: Literal["instant", "daily", "weekly", "never"]


class MessageOut(BaseModel):
    message: str
