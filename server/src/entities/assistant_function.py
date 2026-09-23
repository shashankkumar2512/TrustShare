"""
Assistant Function Entity — TrustShare AI Assistant

Stores LLM function definitions in the database.
Python handlers are registered in code, but their schemas
(parameters, descriptions) live in the DB so they can be updated
without redeployment.

"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON
from sqlalchemy.sql import func

from src.database.core import Base


class AssistantFunction(Base):
    __tablename__ = "assistant_functions"

    id = Column(Integer, primary_key=True, index=True)

    function_name = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    display_name = Column(
        String(150),
        nullable=False,
    )

    description = Column(
        Text,
        nullable=False,
    )

    parameters_schema = Column(
        JSON,
        nullable=False,
    )

    category = Column(
        String(50),
        nullable=False,
        default="general",
    )

    requires_auth = Column(
        Boolean,
        nullable=False,
        default=True,
    )

    requires_admin = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
    )

    # Order in admin UI
    display_order = Column(
        Integer,
        nullable=False,
        default=0,
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
