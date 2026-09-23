# server/src/entities/user.py

from sqlalchemy import Column, Integer, String, Boolean, DateTime, BigInteger, Text
from sqlalchemy.sql import func
from src.database.core import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="member")          # admin | member | guest
    plan = Column(String, default="free")            # free | team | enterprise
    mfa_enabled = Column(Boolean, default=False)
    mfa_secret = Column(String, nullable=True)
    storage_used = Column(BigInteger, default=0)     # bytes
    storage_quota = Column(BigInteger, default=5368709120)  # 5 GB default
    avatar_color = Column(String, default="linear-gradient(135deg,#3b82f6,#8b5cf6)")
    organization = Column(String, nullable=True)
    avatar_url = Column(Text, nullable=True)         # Text holds full base64 images
    is_active = Column(Boolean, default=True)
    notification_preferences = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())