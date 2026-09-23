# server/src/analytics/models/analytics_event.py
"""
Central event log for the entire analytics system.
Every user action worth tracking (login, upload, download, share, security event)
gets an entry here.
"""

from sqlalchemy import (
    Column, Integer, String,
    DateTime, ForeignKey, JSON, Index,
)
from sqlalchemy.sql import func
from src.database.core import Base


class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"

    id               = Column(Integer, primary_key=True, index=True)
    event_type       = Column(String(50),  nullable=False, index=True)
    user_id          = Column(Integer, ForeignKey("users.id"),       nullable=True)
    file_id          = Column(Integer, ForeignKey("files.id"),       nullable=True)
    share_link_id    = Column(Integer, ForeignKey("share_links.id"), nullable=True)
    status           = Column(String(20),  nullable=False, default="SUCCESS")
    ip_address       = Column(String(100), nullable=True)
    browser          = Column(String(100), nullable=True)
    operating_system = Column(String(100), nullable=True)
    device           = Column(String(100), nullable=True)
    country          = Column(String(100), nullable=True)
    city             = Column(String(100), nullable=True)
    event_metadata   = Column(JSON,        nullable=True)
    created_at       = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
    )


# Composite indexes for common analytics queries
Index(
    "idx_ae_type_created",
    AnalyticsEvent.event_type,
    AnalyticsEvent.created_at,
)

Index(
    "idx_ae_status_created",
    AnalyticsEvent.status,
    AnalyticsEvent.created_at,
)

Index(
    "idx_ae_type_status_created",
    AnalyticsEvent.event_type,
    AnalyticsEvent.status,
    AnalyticsEvent.created_at,
)