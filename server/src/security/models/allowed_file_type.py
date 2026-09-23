from sqlalchemy import (
    Boolean,
    Column,
    Integer,
    String,
)

from src.database.core import Base


class AllowedFileType(Base):
    __tablename__ = "allowed_file_types"

    id = Column(Integer, primary_key=True, index=True)

    extension = Column(
        String,
        unique=True,
        nullable=False,
    )

    mime_type = Column(
        String,
        nullable=False,
    )

    description = Column(
        String,
        nullable=True,
    )

    is_active = Column(
        Boolean,
        default=True,
    )