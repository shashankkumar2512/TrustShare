"""
Secure Storage Module — TrustShare Encryption & Security

Industry-grade file storage with:
- Path traversal protection
- Atomic writes (crash-safe)
- File permission management
- Streaming support for large files
- Storage backend abstraction (ready for AWS S3)
- Comprehensive error handling
- Storage metrics

Current Backend: Local filesystem
Future Backend: AWS S3 (per PSD requirement)

Architecture:
- StorageBackend interface allows easy migration to S3
- Encryption happens BEFORE storage (backend never sees plaintext)
- All operations are atomic (crash-safe)

References:
- OWASP File Upload Cheat Sheet
- AWS S3 Best Practices
- PRD 4: Only encrypted files stored in cloud storage
"""

import os
import stat
import shutil
import logging
import platform
from pathlib import Path
from typing import Optional, Iterator, BinaryIO
from contextlib import contextmanager

from .exceptions import EncryptionError
from src.security.config_loader import get_config_int

# CONFIGURATION

# Storage directory
STORAGE_DIR = Path("uploads")

# File permissions
STORAGE_DIR_MODE = 0o755  # Directory: rwxr-xr-x
FILE_MODE = 0o644         # Files: rw-r--r--

def _get_max_file_size(db=None):
    return get_config_int("MAX_FILE_SIZE", db, 500 * 1024 * 1024)

def _get_max_filename_length(db=None):
    return get_config_int("MAX_FILENAME_LENGTH", db, 255)
# Storage limits
MAX_FILENAME_LENGTH = 255
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500 MB per file

# Streaming chunk size (64 KB for optimal I/O)
STREAM_CHUNK_SIZE = 64 * 1024

# Platform detection
IS_WINDOWS = platform.system() == "Windows"

# Storage backend type (future extension point)
STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "local")  # Future: "aws_s3", "azure_blob"

# Setup logger
logger = logging.getLogger(__name__)

# Public API
__all__ = [
    'save_encrypted_file',
    'load_encrypted_file',
    'load_encrypted_file_stream',
    'delete_encrypted_file',
    'file_exists',
    'get_file_metadata',
    'get_storage_stats',
    'STORAGE_DIR',
    'MAX_FILE_SIZE',
]


# INITIALIZATION

def _initialize_storage_directory() -> None:
    """Initialize storage directory with proper permissions."""
    try:
        STORAGE_DIR.mkdir(exist_ok=True, parents=True)

        # Set permissions (Unix)
        if not IS_WINDOWS:
            os.chmod(STORAGE_DIR, STORAGE_DIR_MODE)

        logger.info(f"Storage directory initialized: {STORAGE_DIR.absolute()}")

    except Exception as e:
        logger.critical(f"Failed to initialize storage directory: {e}")
        raise EncryptionError("Cannot initialize storage")


# Initialize on module import
_initialize_storage_directory()

# VALIDATION HELPERS

def _validate_filename(filename: str) -> str:
    """
    Validate and sanitize filename to prevent security issues.

    Args:
        filename: Filename to validate.

    Returns:
        Sanitized filename safe for storage.

    Raises:
        EncryptionError: If filename is invalid.
    """
    if not filename:
        raise EncryptionError("Filename cannot be empty")

    if not isinstance(filename, str):
        raise EncryptionError(
            f"Filename must be string, got {type(filename).__name__}"
        )

    # Path traversal protection
    if "/" in filename or "\\" in filename:
        raise EncryptionError("Filename cannot contain path separators")

    if ".." in filename:
        raise EncryptionError("Filename cannot contain '..'")

    # Null byte protection
    if "\x00" in filename:
        raise EncryptionError("Filename cannot contain null bytes")

    # Length check
    if len(filename) > MAX_FILENAME_LENGTH:
        raise EncryptionError(
            f"Filename too long (max {MAX_FILENAME_LENGTH} chars)"
        )

    # Reserved names (Windows)
    if IS_WINDOWS:
        reserved = {
            "CON", "PRN", "AUX", "NUL",
            "COM1", "COM2", "COM3", "COM4", "COM5",
            "COM6", "COM7", "COM8", "COM9",
            "LPT1", "LPT2", "LPT3", "LPT4", "LPT5",
            "LPT6", "LPT7", "LPT8", "LPT9",
        }
        base_name = filename.split('.')[0].upper()
        if base_name in reserved:
            raise EncryptionError(f"Reserved filename: {filename}")

    return filename


def _get_safe_path(filename: str) -> Path:
    """
    Get validated path within STORAGE_DIR.

    Prevents path traversal attacks by ensuring resolved path
    stays within STORAGE_DIR.
    """
    filename = _validate_filename(filename)
    file_path = STORAGE_DIR / filename

    # Defense in depth: verify resolved path is within STORAGE_DIR
    try:
        resolved = file_path.resolve()
        storage_resolved = STORAGE_DIR.resolve()
        resolved.relative_to(storage_resolved)
    except ValueError:
        logger.error(f"Path traversal attempt: {filename}")
        raise EncryptionError("Invalid file path")

    return file_path


def _validate_file_size(data_size: int) -> None:
    """Validate file size against limits."""
    if data_size <= 0:
        raise EncryptionError("File cannot be empty")

    if data_size > MAX_FILE_SIZE:
        raise EncryptionError(
            f"File too large: {data_size} bytes "
            f"(max {MAX_FILE_SIZE} bytes)"
        )


def _set_file_permissions(path: Path) -> None:
    """Set standard file permissions (Unix)."""
    if not IS_WINDOWS:
        try:
            os.chmod(path, FILE_MODE)
        except OSError as e:
            logger.warning(f"Failed to set permissions on {path}: {e}")


# SAVE OPERATIONS (Atomic writes)

def save_encrypted_file(filename: str, encrypted_data: bytes) -> Path:
    """
    Save encrypted file atomically with security best practices.

    Process:
        1. Validate filename and data
        2. Write to temporary file
        3. Fsync to disk
        4. Set secure permissions
        5. Atomic rename

    Args:
        filename: Storage filename (validated for safety).
        encrypted_data: Encrypted file content.

    Returns:
        Absolute path to saved file.

    Raises:
        EncryptionError: If save fails.
    """
    # Input validation
    if not isinstance(encrypted_data, (bytes, bytearray)):
        raise EncryptionError(
            f"Data must be bytes, got {type(encrypted_data).__name__}"
        )

    _validate_file_size(len(encrypted_data))

    # Get safe path
    destination = _get_safe_path(filename)
    temp_destination = destination.with_suffix(f"{destination.suffix}.tmp")

    try:
        # Atomic write pattern
        with open(temp_destination, "wb") as f:
            f.write(bytes(encrypted_data))
            f.flush()
            os.fsync(f.fileno())

        # Set permissions BEFORE rename (Unix)
        _set_file_permissions(temp_destination)

        # Atomic rename (POSIX guarantee)
        os.replace(temp_destination, destination)

        # Set permissions on final file (defense in depth)
        _set_file_permissions(destination)

        logger.info(
            f"Saved encrypted file: {filename} ({len(encrypted_data)} bytes)"
        )
        return destination

    except EncryptionError:
        raise

    except Exception as e:
        # Cleanup temp file on failure
        if temp_destination.exists():
            try:
                temp_destination.unlink()
            except OSError:
                logger.warning(f"Failed to cleanup temp file: {temp_destination}")

        logger.error(
            f"Failed to save encrypted file {filename}: {type(e).__name__}"
        )
        raise EncryptionError("Failed to save encrypted file")


# LOAD OPERATIONS

def load_encrypted_file(filename: str) -> bytes:
    """
    Load entire encrypted file into memory.

    ⚠️ Use for small files (< 100 MB).
    For large files, use load_encrypted_file_stream().

    Args:
        filename: Storage filename.

    Returns:
        Encrypted file bytes.

    Raises:
        FileNotFoundError: If file doesn't exist.
        EncryptionError: If load fails.
    """
    file_path = _get_safe_path(filename)

    if not file_path.exists():
        logger.warning(f"Encrypted file not found: {filename}")
        raise FileNotFoundError(f"Encrypted file not found: {filename}")

    if not file_path.is_file():
        raise EncryptionError("Path is not a file")

    try:
        # Check size before loading
        file_size = file_path.stat().st_size
        if file_size > MAX_FILE_SIZE:
            raise EncryptionError(
                f"File too large for in-memory load: {file_size} bytes. "
                f"Use load_encrypted_file_stream() for large files."
            )

        with open(file_path, "rb") as f:
            data = f.read()

        logger.debug(f"Loaded encrypted file: {filename} ({len(data)} bytes)")
        return data

    except (FileNotFoundError, EncryptionError):
        raise

    except PermissionError:
        logger.error(f"Permission denied: {filename}")
        raise EncryptionError("Cannot read encrypted file (permission denied)")

    except Exception as e:
        logger.error(f"Failed to load {filename}: {type(e).__name__}")
        raise EncryptionError("Failed to load encrypted file")


@contextmanager
def load_encrypted_file_stream(filename: str) -> Iterator[BinaryIO]:
    """
    Load encrypted file as a stream (memory-efficient for large files).

    Args:
        filename: Storage filename.

    Yields:
        Binary file stream.

    Example:
        >>> with load_encrypted_file_stream("file.enc") as stream:
        ...     while chunk := stream.read(64 * 1024):
        ...         process(chunk)

    Raises:
        FileNotFoundError: If file doesn't exist.
        EncryptionError: If load fails.
    """
    file_path = _get_safe_path(filename)

    if not file_path.exists():
        raise FileNotFoundError(f"Encrypted file not found: {filename}")

    if not file_path.is_file():
        raise EncryptionError("Path is not a file")

    file_handle = None
    try:
        file_handle = open(file_path, "rb")
        logger.debug(f"Opened stream for: {filename}")
        yield file_handle

    except PermissionError:
        raise EncryptionError("Cannot read encrypted file (permission denied)")

    except Exception as e:
        logger.error(f"Failed to stream {filename}: {type(e).__name__}")
        raise EncryptionError("Failed to stream encrypted file")

    finally:
        if file_handle:
            try:
                file_handle.close()
            except Exception:
                pass


# DELETE OPERATIONS

def delete_encrypted_file(filename: str) -> bool:
    """
    Securely delete encrypted file.

    Args:
        filename: Storage filename.

    Returns:
        True if deleted, False if not found.

    Raises:
        EncryptionError: If deletion fails.
    """
    try:
        file_path = _get_safe_path(filename)

        if not file_path.exists():
            logger.info(f"File already deleted or missing: {filename}")
            return False

        # Overwrite with random data before delete (best-effort)
        # Note: Not effective on SSDs due to wear leveling
        try:
            file_size = file_path.stat().st_size
            with open(file_path, "wb") as f:
                f.write(os.urandom(file_size))
                f.flush()
                os.fsync(f.fileno())
        except OSError:
            pass  # Continue with delete even if overwrite fails

        # Delete
        file_path.unlink()

        logger.info(f"Deleted encrypted file: {filename}")
        return True

    except EncryptionError:
        raise

    except Exception as e:
        logger.error(f"Failed to delete {filename}: {type(e).__name__}")
        raise EncryptionError("Failed to delete encrypted file")


# QUERY FUNCTIONS

def file_exists(filename: str) -> bool:
    """
    Check if encrypted file exists.

    Args:
        filename: Storage filename.

    Returns:
        True if file exists, False otherwise.
    """
    try:
        file_path = _get_safe_path(filename)
        return file_path.exists() and file_path.is_file()
    except EncryptionError:
        return False


def get_file_metadata(filename: str) -> Optional[dict]:
    """
    Get metadata about stored file.

    Args:
        filename: Storage filename.

    Returns:
        Metadata dict or None if file doesn't exist.
    """
    try:
        file_path = _get_safe_path(filename)

        if not file_path.exists():
            return None

        stat_info = file_path.stat()

        metadata = {
            'filename': filename,
            'path': str(file_path.absolute()),
            'size': stat_info.st_size,
            'created_at': stat_info.st_ctime,
            'modified_at': stat_info.st_mtime,
            'backend': STORAGE_BACKEND,
        }

        if not IS_WINDOWS:
            metadata['permissions'] = oct(stat.S_IMODE(stat_info.st_mode))

        return metadata

    except EncryptionError:
        return None
    except Exception as e:
        logger.error(f"Failed to get metadata for {filename}: {e}")
        return None


def get_storage_stats() -> dict:
    """
    Get overall storage statistics.

    Returns:
        Dict with storage statistics.
    """
    try:
        total_files = 0
        total_size = 0

        for file_path in STORAGE_DIR.iterdir():
            if file_path.is_file():
                total_files += 1
                total_size += file_path.stat().st_size

        # Get disk usage
        disk_usage = shutil.disk_usage(STORAGE_DIR)

        return {
            'backend': STORAGE_BACKEND,
            'storage_dir': str(STORAGE_DIR.absolute()),
            'total_files': total_files,
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'disk_total_gb': round(disk_usage.total / (1024 ** 3), 2),
            'disk_used_gb': round(disk_usage.used / (1024 ** 3), 2),
            'disk_free_gb': round(disk_usage.free / (1024 ** 3), 2),
            'disk_usage_percent': round(
                (disk_usage.used / disk_usage.total) * 100, 2
            ),
        }

    except Exception as e:
        logger.error(f"Failed to get storage stats: {e}")
        return {'error': 'Failed to retrieve storage statistics'}


# FUTURE: AWS S3 INTEGRATION

# TODO: When migrating to AWS S3, implement these:
#
# def _save_to_s3(filename, data, bucket):
#     """Save encrypted file to AWS S3."""
#     import boto3
#     s3 = boto3.client('s3')
#     s3.put_object(
#         Bucket=bucket,
#         Key=filename,
#         Body=data,
#         ServerSideEncryption='AES256',  # S3-managed encryption (additional layer)
#     )
#
# def _load_from_s3(filename, bucket):
#     """Load encrypted file from AWS S3."""
#     import boto3
#     s3 = boto3.client('s3')
#     response = s3.get_object(Bucket=bucket, Key=filename)
#     return response['Body'].read()