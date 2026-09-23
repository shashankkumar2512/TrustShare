# server/src/analytics/models/event_status.py
"""
Master lookup table for event statuses (SUCCESS / FAILED / WARNING).
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from src.database.core import Base


class AnalyticsEventStatus(Base):
    __tablename__ = "analytics_event_statuses"

    id          = Column(Integer, primary_key=True, index=True)
    code        = Column(String(30),  unique=True, nullable=False)
    name        = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    is_active   = Column(Boolean, default=True, nullable=False)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())