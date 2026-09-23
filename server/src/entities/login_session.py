from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.sql import func
from src.database.core import Base


class LoginSession(Base):
    __tablename__ = "login_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    device_name = Column(String, nullable=True)
    browser_name = Column(String, nullable=True)
    device_type = Column(String, nullable=True)  # desktop | mobile | tablet | bot | unknown
    ip_address = Column(String, nullable=True)
    location = Column(String, nullable=True)
    last_active = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    refresh_token = Column(String, nullable=True)
    is_current = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
