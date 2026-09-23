from sqlalchemy import Column, Integer, String, Boolean, BigInteger, ForeignKey, DateTime
from sqlalchemy.sql import func
from src.database.core import Base


class FileVersion(Base):
    __tablename__ = "file_versions"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("files.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    stored_name = Column(String, nullable=False)
    mimetype = Column(String, nullable=False, default="application/octet-stream")
    size = Column(BigInteger, nullable=False, default=0)
    encrypted = Column(Boolean, default=True)
    hash_sha256 = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)