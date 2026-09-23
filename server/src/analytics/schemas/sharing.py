# server/src/analytics/schemas/sharing.py

from pydantic import BaseModel
from typing import List


class TopSharedFile(BaseModel):
    rank:      int
    name:      str
    opens:     int
    downloads: int
    pct:       float


class DepartmentShare(BaseModel):
    name:  str
    value: float
    color: str


class SharingAnalyticsResponse(BaseModel):
    total_links:    int
    active_links:   int
    inactive_links: int
    total_views:    int
    new_this_week:  int = 0
    top_files:      List[TopSharedFile]
    by_department:  List[DepartmentShare]