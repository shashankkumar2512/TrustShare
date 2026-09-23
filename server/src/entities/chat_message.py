"""
Chat Message Entity — TrustShare AI Assistant

"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.database.core import Base


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)

    conversation_id = Column(
        Integer,
        ForeignKey("chat_conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    role = Column(
        String(20),
        nullable=False,
    )

    content = Column(
        Text,
        nullable=True,
    )

    function_name = Column(
        String(100),
        nullable=True,
    )

    function_result = Column(
        JSON,
        nullable=True,
    )

    tokens_used = Column(
        Integer,
        nullable=True,
    )

    model_used = Column(
        String(100),
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
    )

    conversation = relationship(
        "ChatConversation",
        back_populates="messages",
    )
