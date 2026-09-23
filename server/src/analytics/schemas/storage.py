# server/src/analytics/schemas/storage.py

from pydantic import BaseModel
from typing import List


class StorageTrendPoint(BaseModel):
    month: str
    gb: float


class StorageResponse(BaseModel):
    total_users:        int
    storage_used:       int
    storage_quota:      int
    storage_percentage: float
    storage_used_gb:    float
    storage_quota_gb:   float
    trend:              List[StorageTrendPoint]