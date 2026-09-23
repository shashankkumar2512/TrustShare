"""
Upload Validation Module — TrustShare Encryption & Security

Industry-grade file upload validation with:
- MIME type validation (whitelist)
- File extension validation
- Magic bytes verification (real file type detection)
- Size limits (configurable)
- Filename sanitization
- Content scanning hooks (future antivirus)
- Detailed validation errors

References:
- OWASP File Upload Cheat Sheet
- NIST SP 800-53 SI-3 (Malicious Code Protection)
- PRD 4.ii: File type, size, and permissions validation
"""

import re
import logging
import mimetypes
from pathlib import Path
from typing import Optional, Set, Tuple
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

# CONFIGURATION

# File size limits (bytes)
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB per file
MIN_FILE_SIZE = 1  # At least 1 byte
CHUNK_SIZE_FOR_VALIDATION = 8192  # 8KB for magic bytes detection

# Filename limits
MAX_FILENAME_LENGTH = 255
MIN_FILENAME_LENGTH = 1

# Reserved Windows filenames
WINDOWS_RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    "COM1",
    "COM2",
    "COM3",
    "COM4",
    "COM5",
    "COM6",
    "COM7",
    "COM8",
    "COM9",
    "LPT1",
    "LPT2",
    "LPT3",
    "LPT4",
    "LPT5",
    "LPT6",
    "LPT7",
    "LPT8",
    "LPT9",
}

# Setup logger
logger = logging.getLogger(__name__)

# Public API
__all__ = [
    "validate_upload",
    "validate_filename",
    "sanitize_filename",
    "validate_file_size",
    "validate_file_extension",
    "validate_mime_type",
    "detect_file_type",
    "get_file_extension",
    "MAX_FILE_SIZE",
    "MIN_FILE_SIZE",
]

# MAGIC BYTES (File Signature Detection)

# Common file signatures (magic bytes)
# Format: {extension: [(offset, magic_bytes), ...]}
MAGIC_BYTES_MAP = {
    # Images
    "jpg": [(0, b"\xff\xd8\xff")],
    "jpeg": [(0, b"\xff\xd8\xff")],
    "png": [(0, b"\x89PNG\r\n\x1a\n")],
    "gif": [(0, b"GIF87a"), (0, b"GIF89a")],
    "webp": [(0, b"RIFF"), (8, b"WEBP")],
    "bmp": [(0, b"BM")],
    "svg": [(0, b"<?xml"), (0, b"<svg")],
    # Documents
    "pdf": [(0, b"%PDF-")],
    "doc": [(0, b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1")],  # MS Office old
    "docx": [(0, b"PK\x03\x04")],  # ZIP-based
    "xls": [(0, b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1")],
    "xlsx": [(0, b"PK\x03\x04")],
    "ppt": [(0, b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1")],
    "pptx": [(0, b"PK\x03\x04")],
    # Archives
    "zip": [(0, b"PK\x03\x04"), (0, b"PK\x05\x06"), (0, b"PK\x07\x08")],
    "rar": [(0, b"Rar!\x1a\x07\x00")],
    "7z": [(0, b"7z\xbc\xaf\x27\x1c")],
    "tar": [(257, b"ustar")],
    "gz": [(0, b"\x1f\x8b")],
    # Media
    "mp3": [(0, b"ID3"), (0, b"\xff\xfb")],
    "mp4": [(4, b"ftyp")],
    "avi": [(0, b"RIFF"), (8, b"AVI ")],
    "mkv": [(0, b"\x1a\x45\xdf\xa3")],
    # Text (no magic bytes, but common)
    "txt": [],  # No signature
    "csv": [],  # No signature
    "json": [(0, b"{"), (0, b"[")],
    "xml": [(0, b"<?xml"), (0, b"<")],
}

# FILENAME VALIDATION


def validate_filename(filename: str) -> None:
    """
    Validate filename for security and correctness.

    Args:
        filename: The filename to validate.

    Raises:
        HTTPException: If filename is invalid.
    """
    if not filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Filename cannot be empty"
        )

    if not isinstance(filename, str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Filename must be a string"
        )

    # Length validation
    if len(filename) < MIN_FILENAME_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Filename too short (min {MIN_FILENAME_LENGTH} char)",
        )

    if len(filename) > MAX_FILENAME_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Filename too long (max {MAX_FILENAME_LENGTH} chars)",
        )

    # Path traversal protection
    if "/" in filename or "\\" in filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename cannot contain path separators",
        )

    if ".." in filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename cannot contain '..'",
        )

    # Null byte protection
    if "\x00" in filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename cannot contain null bytes",
        )

    # Control character protection
    if any(ord(c) < 32 for c in filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename contains invalid control characters",
        )

    # Windows reserved names
    base_name = filename.split(".")[0].upper()
    if base_name in WINDOWS_RESERVED_NAMES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Filename '{filename}' is a reserved system name",
        )

    # Must have an extension
    if "." not in filename:
        logger.warning(f"File uploaded without extension: {filename}")


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing/replacing unsafe characters.

    Args:
        filename: Filename to sanitize.

    Returns:
        Sanitized filename safe for storage.
    """
    if not filename:
        return "unnamed_file"

    # Get just the filename part (remove path)
    filename = Path(filename).name

    # Replace unsafe characters with underscore
    # Invalid: < > : " / \ | ? * and control chars
    filename = re.sub(r'[<>:"/\\|?*\x00-\x1F]', "_", filename)

    # Remove leading/trailing whitespace and dots
    filename = filename.strip(". ")

    # Collapse multiple underscores
    filename = re.sub(r"_+", "_", filename)

    # Ensure filename is not empty after sanitization
    if not filename or filename == "_":
        filename = "unnamed_file"

    # Truncate if too long (keep extension)
    if len(filename) > MAX_FILENAME_LENGTH:
        name_parts = filename.rsplit(".", 1)
        if len(name_parts) == 2:
            ext = name_parts[1]
            max_name = MAX_FILENAME_LENGTH - len(ext) - 1
            filename = f"{name_parts[0][:max_name]}.{ext}"
        else:
            filename = filename[:MAX_FILENAME_LENGTH]

    return filename


def get_file_extension(filename: str) -> str:
    """
    Get lowercase file extension without dot.

    Args:
        filename: The filename.

    Returns:
        Lowercase extension (e.g., "pdf") or empty string.
    """
    if not filename or "." not in filename:
        return ""
    return filename.rsplit(".", 1)[-1].lower()


# SIZE VALIDATION


def validate_file_size(size: int, max_size: Optional[int] = None) -> None:
    """
    Validate file size against limits.

    Args:
        size: File size in bytes.
        max_size: Optional custom max size (default: MAX_FILE_SIZE).

    Raises:
        HTTPException: If size is invalid.
    """
    if size is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="File size is required"
        )

    if not isinstance(size, int):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size must be an integer",
        )

    if size < MIN_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="File is empty or invalid"
        )

    limit = max_size if max_size else MAX_FILE_SIZE

    if size > limit:
        size_mb = size / (1024 * 1024)
        limit_mb = limit / (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large ({size_mb:.1f} MB). Maximum: {limit_mb:.0f} MB",
        )


# EXTENSION & MIME TYPE VALIDATION


def _get_allowed_extensions(db: Session) -> Set[str]:
    """
    Get allowed file extensions from database.

    Args:
        db: Database session.

    Returns:
        Set of allowed extensions (lowercase, without dots).
    """
    try:
        from src.security.models.allowed_file_type import AllowedFileType

        allowed = (
            db.query(AllowedFileType.extension)
            .filter(AllowedFileType.is_active == True)
            .all()
        )
        return {ext[0].lower().lstrip(".") for ext in allowed}
    except Exception as e:
        logger.error(f"Failed to load allowed extensions from DB: {e}")
        # Fallback to safe defaults if DB fails
        return {
            "pdf",
            "doc",
            "docx",
            "xls",
            "xlsx",
            "ppt",
            "pptx",
            "txt",
            "csv",
            "json",
            "xml",
            "jpg",
            "jpeg",
            "png",
            "gif",
            "webp",
            "bmp",
            "zip",
            "tar",
            "gz",
            "mp3",
            "mp4",
            "avi",
            "mkv",
        }


def _get_allowed_mime_types(db: Session) -> Set[str]:
    """Get allowed MIME types from database."""
    try:
        from src.security.models.allowed_file_type import AllowedFileType

        allowed = (
            db.query(AllowedFileType.mime_type)
            .filter(AllowedFileType.is_active == True)
            .all()
        )
        return {mime[0].lower() for mime in allowed if mime[0]}
    except Exception:
        # Fallback
        return {
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "image/jpeg",
            "image/png",
            "image/gif",
            "image/webp",
            "text/plain",
            "text/csv",
            "application/zip",
            "application/x-tar",
            "application/gzip",
            "audio/mpeg",
            "video/mp4",
        }


def validate_file_extension(filename: str, allowed_extensions: Set[str]) -> None:
    """
    Validate file has allowed extension.

    Args:
        filename: The filename.
        allowed_extensions: Set of allowed extensions.

    Raises:
        HTTPException: If extension not allowed.
    """
    ext = get_file_extension(filename)

    if not ext:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must have an extension",
        )

    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type '.{ext}' is not allowed. "
            f"Allowed types: {', '.join(sorted(allowed_extensions))}",
        )


# ── MIME type aliases (handle browser/OS variants) ──────────────────────
# Different browsers and OSs send different MIME types for the same file.
# This map normalizes them to their canonical forms found in the DB.
MIME_ALIASES = {
    # Windows sends "x-zip-compressed" for both ZIP and RAR files
    "application/x-zip-compressed": ["application/zip", "application/x-rar-compressed"],
    # RAR variants across systems
    "application/vnd.rar": ["application/x-rar-compressed"],
    "application/x-rar": ["application/x-rar-compressed"],
    "application/rar": ["application/x-rar-compressed"],
    # 7-Zip variants
    "application/x-7z": ["application/x-7z-compressed"],
    "application/7z": ["application/x-7z-compressed"],
    # Image variants
    "image/jpg": ["image/jpeg"],
    "image/pjpeg": ["image/jpeg"],  # Progressive JPEG (old IE)
    # Document variants
    "application/x-pdf": ["application/pdf"],
    "text/pdf": ["application/pdf"],
    # Text variants
    "application/xml": ["text/xml"],
    "text/xml": ["application/xml"],
    "text/json": ["application/json"],
    # Media variants
    "audio/mp3": ["audio/mpeg"],
    "audio/x-wav": ["audio/wav"],
    "audio/wave": ["audio/wav"],
    "video/mpeg4": ["video/mp4"],
    # Generic fallback (browsers sometimes send this for archives)
    "application/octet-stream": [],  # Handled separately — allow with extension check
}


def validate_mime_type(mime_type: str, allowed_mimes: Set[str]) -> None:
    """
    Validate MIME type is allowed.

    Normalizes common browser/OS MIME type variants before checking.
    Example: Windows sends 'application/x-zip-compressed' for RAR files.

    Args:
        mime_type: MIME type to validate.
        allowed_mimes: Set of allowed MIME types.

    Raises:
        HTTPException: If MIME type not allowed after normalization.
    """
    if not mime_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="MIME type is required"
        )

    mime_lower = mime_type.lower().split(";")[0].strip()

    if mime_lower in allowed_mimes:
        return

    if mime_lower in MIME_ALIASES:
        for canonical_mime in MIME_ALIASES[mime_lower]:
            if canonical_mime in allowed_mimes:
                logger.info(f"MIME alias accepted: '{mime_type}' → '{canonical_mime}'")
                return

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"MIME type '{mime_type}' is not allowed",
    )


# MAGIC BYTES DETECTION (Real File Type)


def detect_file_type(file_bytes: bytes) -> Optional[str]:
    """
    Detect actual file type from magic bytes (file signature).

    This is more reliable than trusting the extension since
    users can rename malicious files to appear safe.

    Args:
        file_bytes: First few bytes of the file.

    Returns:
        Detected extension or None if unknown.
    """
    if not file_bytes:
        return None

    for extension, signatures in MAGIC_BYTES_MAP.items():
        if not signatures:  # No magic bytes defined
            continue

        for offset, magic in signatures:
            if len(file_bytes) >= offset + len(magic):
                if file_bytes[offset : offset + len(magic)] == magic:
                    return extension

    return None


def verify_file_type_matches(
    file_bytes: bytes,
    claimed_extension: str,
) -> bool:
    """
    Verify that file's actual type matches claimed extension.

    Prevents renaming .exe to .pdf attacks.

    Args:
        file_bytes: First bytes of file (at least 512).
        claimed_extension: Extension user claims.

    Returns:
        True if types match, False otherwise.
    """
    detected = detect_file_type(file_bytes)
    claimed = claimed_extension.lower().lstrip(".")

    # Some formats share magic bytes (Office docs)
    magic_equivalents = {
        "docx": ["docx", "xlsx", "pptx", "zip"],  # All ZIP-based
        "xlsx": ["docx", "xlsx", "pptx", "zip"],
        "pptx": ["docx", "xlsx", "pptx", "zip"],
        "zip": ["docx", "xlsx", "pptx", "zip"],
        "doc": ["doc", "xls", "ppt"],  # All OLE
        "xls": ["doc", "xls", "ppt"],
        "ppt": ["doc", "xls", "ppt"],
    }

    if detected is None:
        # Extensions without magic bytes (txt, csv) - allow
        return claimed in {"txt", "csv"}

    # Check if detected matches claimed
    if detected == claimed:
        return True

    # Check equivalents
    if claimed in magic_equivalents:
        return detected in magic_equivalents[claimed]

    return False


# MAIN VALIDATION FUNCTION (Backward Compatible)


def validate_upload(
    db: Session,
    upload: UploadFile,
    file_size: int,
) -> None:
    """
    Complete validation of uploaded file.

    Validates:
        1. Filename (length, characters, path traversal)
        2. File size (min/max)
        3. File extension (whitelist)
        4. MIME type (whitelist)
        5. Magic bytes (real file type verification)

    Args:
        db: Database session.
        upload: FastAPI UploadFile.
        file_size: File size in bytes.

    Raises:
        HTTPException: If validation fails at any step.
    """
    if not upload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No file provided"
        )

    filename = upload.filename or "unnamed"

    # Step 1: Validate filename
    validate_filename(filename)

    # Step 2: Validate size
    validate_file_size(file_size)

    # Step 3: Get allowed types from DB
    allowed_extensions = _get_allowed_extensions(db)
    allowed_mimes = _get_allowed_mime_types(db)

    # Step 4: Validate extension
    validate_file_extension(filename, allowed_extensions)

    # Step 5: Validate MIME type
    mime_type = upload.content_type or mimetypes.guess_type(filename)[0]
    if mime_type:
        validate_mime_type(mime_type, allowed_mimes)

    # Step 6: Magic bytes verification (optional but recommended)
    try:
        # Read first chunk for magic bytes
        upload.file.seek(0)
        first_chunk = upload.file.read(CHUNK_SIZE_FOR_VALIDATION)
        upload.file.seek(0)  # Reset for actual upload

        claimed_ext = get_file_extension(filename)
        if claimed_ext and first_chunk:
            if not verify_file_type_matches(first_chunk, claimed_ext):
                logger.warning(
                    f"File type mismatch: {filename} claims .{claimed_ext} "
                    f"but content suggests otherwise"
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File content does not match .{claimed_ext} format",
                )
    except HTTPException:
        raise
    except Exception as e:
        # Don't fail validation if magic bytes check fails
        logger.error(f"Magic bytes check failed: {e}")

    logger.info(f"Upload validated: {filename} " f"({file_size} bytes, {mime_type})")
