from sqlalchemy import Column, Integer, Boolean, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from src.database.core import Base


class NotificationPreference(Base):
    __tablename__ = "notification_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    file_shares = Column(Boolean, default=True)
    downloads = Column(Boolean, default=True)
    security_alerts = Column(Boolean, default=True)
    link_expirations = Column(Boolean, default=True)
    access_changes = Column(Boolean, default=True)
    system_updates = Column(Boolean, default=True)
    digest_frequency = Column(String, default="daily")  # immediate | daily | weekly
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
