# server/src/analytics/schemas/downloads.py

from pydantic import BaseModel
from typing import List


class DownloadTrendItem(BaseModel):
    date:  str
    count: int


class DownloadAnalyticsResponse(BaseModel):
    total_downloads:      int
    today_downloads:      int
    this_month_downloads: int   = 0
    transferred_bytes:    int   = 0
    transferred_gb:       float = 0
    transferred_mb:       float = 0
    weekly_downloads:     List[DownloadTrendItem]