# server/src/analytics/seed/seed_severity_map.py
"""
Severity mapping — maps event_metadata.severity_key to UI severity level.
Mentor can add new mappings via DB without touching code.
"""

from sqlalchemy.orm import Session
from src.analytics.models.severity_map import AnalyticsSeverityMap


SEVERITY_ROWS = [
    {"severity_key": "brute_force",    "severity": "blocked", "display_label": "Brute Force Attack",   "description": "Multiple failed login attempts detected"},
    {"severity_key": "blocked",        "severity": "blocked", "display_label": "Access Blocked",       "description": "Access explicitly blocked"},
    {"severity_key": "new_device",     "severity": "flagged", "display_label": "New Device Login",     "description": "Login from previously unseen device"},
    {"severity_key": "login_failed",   "severity": "flagged", "display_label": "Failed Login",         "description": "Single failed login"},
    {"severity_key": "external_link",  "severity": "warn",    "display_label": "External Share Link",  "description": "Shared file accessed via external link"},
    {"severity_key": "unusual_access", "severity": "warn",    "display_label": "Unusual Access",       "description": "Access pattern deviates from normal behavior"},
    {"severity_key": "admin_role",     "severity": "info",    "display_label": "Admin Role Change",    "description": "User role changed to admin"},
    {"severity_key": "default",        "severity": "info",    "display_label": "Info",                 "description": "Default fallback severity"},
]


def seed_severity_map(db: Session):
    for item in SEVERITY_ROWS:
        exists = (
            db.query(AnalyticsSeverityMap)
            .filter(AnalyticsSeverityMap.severity_key == item["severity_key"])
            .first()
        )
        if not exists:
            db.add(AnalyticsSeverityMap(**item))
    db.commit()