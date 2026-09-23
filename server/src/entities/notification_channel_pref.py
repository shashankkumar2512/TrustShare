from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, UniqueConstraint

from src.database.core import Base


class NotificationChannelPreference(Base):
    __tablename__ = "notification_channel_preferences"
    __table_args__ = (UniqueConstraint("user_id", "activity", name="uq_notification_channel_user_activity"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    activity = Column(String, nullable=False)
    in_app = Column(Boolean, nullable=False, default=True)
    email = Column(Boolean, nullable=False, default=False)
