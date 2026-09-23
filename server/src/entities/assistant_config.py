"""
Assistant Configuration Entity — TrustShare AI Assistant

Stores all AI assistant configuration (LLM provider, model, API keys,
rate limits, feature flags) in the database.
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.sql import func

from src.database.core import Base


class AssistantConfig(Base):
    __tablename__ = "assistant_config"

    id = Column(Integer, primary_key=True, index=True)

    config_key = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    config_value = Column(
        Text,
        nullable=True,
    )

    config_type = Column(
        String(20),
        nullable=False,
        default="string",
    )

    description = Column(
        Text,
        nullable=True,
    )

    is_secret = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    is_editable = Column(
        Boolean,
        nullable=False,
        default=True,
    )

    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
    )

    category = Column(
        String(50),
        nullable=False,
        default="general",
    )

    display_order = Column(
        Integer,
        nullable=False,
        default=0,
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
