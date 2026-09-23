"""
Assistant Prompt Entity — TrustShare AI Assistant

Stores system prompts and canned responses in the database
so they can be tuned without redeployment.

"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.sql import func

from src.database.core import Base


class AssistantPrompt(Base):
    __tablename__ = "assistant_prompts"

    id = Column(Integer, primary_key=True, index=True)

    prompt_key = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    prompt_text = Column(
        Text,
        nullable=False,
    )

    description = Column(
        Text,
        nullable=True,
    )

    version = Column(
        Integer,
        nullable=False,
        default=1,
    )

    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
