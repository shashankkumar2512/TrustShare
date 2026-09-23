# server/src/analytics/schemas/deletes.py

from pydantic import BaseModel


class DeleteAnalyticsResponse(BaseModel):
    total_deletes:      int
    today_deletes:      int
    this_week_deletes:  int = 0
    this_month_deletes: int = 0