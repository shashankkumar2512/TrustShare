from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
)
from sqlalchemy.sql import func

from src.database.core import Base


class AppConfig(Base):
    __tablename__ = "app_config"

    id = Column(Integer, primary_key=True, index=True)

    config_key = Column(
        String,
        unique=True,
        nullable=False,
        index=True,
    )

    config_value = Column(
        String,
        nullable=False,
    )

    description = Column(
        String,
        nullable=True,
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )