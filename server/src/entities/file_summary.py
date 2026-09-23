from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.sql import func

from src.database.core import Base


class FileSummary(Base):
    __tablename__ = "file_summaries"
    __table_args__ = (
        UniqueConstraint(
            "file_id", "source_file_version", "source_checksum", "summary_length",
            "output_language", "output_format", name="uq_file_summary_options",
        ),
        Index("ix_file_summaries_file_version_id", "file_version_id"),
        Index("ix_file_summaries_status", "status"),
        Index("ix_file_summaries_source_checksum", "source_checksum"),
    )

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("files.id"), nullable=False, index=True)
    file_version_id = Column(Integer, nullable=True)
    source_file_version = Column(Integer, nullable=False, default=1)
    requested_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="pending")
    summary_length = Column(String(20), nullable=False)
    output_language = Column(String(20), nullable=False)
    output_format = Column(String(30), nullable=False)
    title = Column(String(255), nullable=True)
    summary_text = Column(Text, nullable=True)
    key_points = Column(JSON, nullable=False, default=list)
    keywords = Column(JSON, nullable=False, default=list)
    provider = Column(String(40), nullable=True)
    model_name = Column(String(255), nullable=True)
    source_checksum = Column(String(64), nullable=False)
    extracted_character_count = Column(BigInteger, nullable=False, default=0)
    processing_time_ms = Column(BigInteger, nullable=True)
    warning_message = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    generated_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
