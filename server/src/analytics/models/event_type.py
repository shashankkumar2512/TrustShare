# server/src/analytics/models/event_type.py
"""
Master lookup table for event types.
Referenced by AnalyticsEvent.event_type.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from src.database.core import Base


class AnalyticsEventType(Base):
    __tablename__ = "analytics_event_types"

    id          = Column(Integer, primary_key=True, index=True)
    code        = Column(String(50),  unique=True, nullable=False)
    name        = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    is_active   = Column(Boolean, default=True, nullable=False)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())