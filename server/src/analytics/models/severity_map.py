# server/src/analytics/models/severity_map.py
"""
DB-driven severity mapping.
Maps a `severity_key` (stored in AnalyticsEvent.event_metadata) to a UI severity.

Example rows:
  brute_force   → blocked
  new_device    → flagged
  external_link → warn
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from src.database.core import Base


class AnalyticsSeverityMap(Base):
    __tablename__ = "analytics_severity_map"

    id            = Column(Integer, primary_key=True, index=True)
    severity_key  = Column(String(100), unique=True, nullable=False, index=True)
    severity      = Column(String(30),  nullable=False)   # blocked | flagged | warn | info
    display_label = Column(String(100), nullable=True)
    description   = Column(String(500), nullable=True)
    is_active     = Column(Boolean, default=True, nullable=False)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())