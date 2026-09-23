# server/src/analytics/models/analytics_config.py
"""
Analytics configuration values stored in DB.
All limits, thresholds, and UI config come from this table.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.sql import func
from src.database.core import Base


class AnalyticsConfig(Base):
    __tablename__ = "analytics_config"

    id          = Column(Integer, primary_key=True, index=True)
    key         = Column(String(100), unique=True, nullable=False, index=True)
    # TEXT allows unlimited length — needed for large JSON configs like UI_CONFIG
    value       = Column(Text, nullable=False)
    description = Column(String(500), nullable=True)
    is_active   = Column(Boolean, default=True, nullable=False)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())
    updated_at  = Column(DateTime(timezone=True), onupdate=func.now())