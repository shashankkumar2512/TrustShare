# server/src/analytics/seed/seed_event_statuses.py

from sqlalchemy.orm import Session
from src.analytics.models.event_status import AnalyticsEventStatus


EVENT_STATUSES = [
    {"code": "SUCCESS", "name": "Success", "description": "Operation completed successfully"},
    {"code": "FAILED",  "name": "Failed",  "description": "Operation failed"},
    {"code": "WARNING", "name": "Warning", "description": "Operation completed with warning"},
]


def seed_event_statuses(db: Session):
    for item in EVENT_STATUSES:
        exists = (
            db.query(AnalyticsEventStatus)
            .filter(AnalyticsEventStatus.code == item["code"])
            .first()
        )
        if not exists:
            db.add(AnalyticsEventStatus(**item))
    db.commit()