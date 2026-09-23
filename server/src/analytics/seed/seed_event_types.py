# server/src/analytics/seed/seed_event_types.py

from sqlalchemy.orm import Session
from src.analytics.models.event_type import AnalyticsEventType


EVENT_TYPES = [
    {"code": "LOGIN",    "name": "User Login",     "description": "User authentication events"},
    {"code": "UPLOAD",   "name": "File Upload",    "description": "File upload events"},
    {"code": "DOWNLOAD", "name": "File Download",  "description": "File download events"},
    {"code": "DELETE",   "name": "File Delete",    "description": "File deletion events"},
    {"code": "SHARE",    "name": "File Share",     "description": "File sharing events"},
    {"code": "SECURITY", "name": "Security Event", "description": "Security and validation events"},
]


def seed_event_types(db: Session):
    for item in EVENT_TYPES:
        exists = (
            db.query(AnalyticsEventType)
            .filter(AnalyticsEventType.code == item["code"])
            .first()
        )
        if not exists:
            db.add(AnalyticsEventType(**item))
    db.commit()