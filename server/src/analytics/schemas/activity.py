# server/src/analytics/schemas/activity.py

from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List


class RecentActivityItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:               int
    event_type:       str
    status:           str
    user_id:          Optional[int]  = None
    user_name:        Optional[str]  = None   # ← NEW
    user_email:       Optional[str]  = None   # ← NEW
    file_id:          Optional[int]  = None
    file_name:        Optional[str]  = None   # ← NEW
    ip_address:       Optional[str]  = None
    created_at:       datetime


class RecentActivityResponse(BaseModel):
    activities: List[RecentActivityItem]


class UserListItem(BaseModel):
    id:    int
    name:  str
    email: str


class UserListResponse(BaseModel):
    users: List[UserListItem]


class SystemStatsResponse(BaseModel):
    # Events
    total_events:     int
    events_1h:        int   = 0
    events_24h:       int
    events_7d:        int   = 0

    # Users
    total_users:      int
    active_users_24h: int   = 0

    # Files & storage
    total_files:      int
    total_storage_mb: float = 0

    # Sharing
    total_shares:     int
    active_shares:    int   = 0

    # Performance
    db_response_ms:   float
    success_rate:     float = 100.0

    # Status
    status:           str
    python_version:   str   = ""
    platform:         str   = ""