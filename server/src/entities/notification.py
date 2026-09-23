from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from src.database.core import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    type = Column(String, nullable=False)
    category = Column(String, nullable=False)
    title = Column(String, nullable=False)
    message = Column(String, nullable=False)
    icon = Column(String, nullable=True)
    is_read = Column(Boolean, default=False)
    resource_id = Column(Integer, nullable=True)
    resource_type = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())