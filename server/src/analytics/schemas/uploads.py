# server/src/analytics/schemas/uploads.py

from pydantic import BaseModel
from typing import List


class UploadTrendItem(BaseModel):
    date: str
    count: int


class VolumeWeekPoint(BaseModel):
    week:      str
    uploads:   int
    downloads: int


class UploadAnalyticsResponse(BaseModel):
    total_uploads:       int
    today_uploads:       int
    this_month_uploads:  int = 0
    last_month_uploads:  int = 0
    change_pct:          int = 0
    weekly_uploads:      List[UploadTrendItem]
    volume_weekly:       List[VolumeWeekPoint]