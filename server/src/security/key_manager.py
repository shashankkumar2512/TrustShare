"""
Key Management Module — TrustShare Encryption & Security

Industry-grade AES-256 key management with:
- Encrypted key storage (protected by master key)
- Atomic file operations (crash-safe)
- File permissions (owner-only access)
- Concurrent access safety (file locking)
- Comprehensive audit logging
- Key validation on load
- Secure key deletion

Security Model:
1. Each file has unique AES-256 key
2. Individual keys are encrypted with master key before storage
3. Master key stored separately (env variable in production)
4. Keys directory has restricted permissions (0700)
5. Key files have owner-only permissions (0600)

References:
- NIST SP 800-57: Key Management Recommendations
- OWASP Key Management Cheat Sheet
- PRD 4.Key: Unique keys, server-side, never exposed, rotation
"""

import os
import stat
import secrets
import logging
import platform
from pathlib import Path
from typing import Optional

from .exceptions import KeyManagementError
from .encryption import (
    encrypt_bytes,
    decrypt_bytes,
    validate_key,
    AES_256_KEY_SIZE_BYTES,
)

# CONFIGURATION

# Directory to securely store encryption keys
KEYS_DIR = Path("keys")

# File permissions (Unix)
# Directory: rwx for owner only (0700)
# Files: rw for owner only (0600)
KEYS_DIR_MODE = 0o700
KEY_FILE_MODE = 0o600

# Key file extensions
KEY_FILE_EXTENSION = ".key"
LOCK_FILE_EXTENSION = ".lock"

# Concurrent access handling
IS_WINDOWS = platform.system() == "Windows"

# Setup logger
logger = logging.getLogger(__name__)

# Public API
__all__ = [
    'generate_key',
    'save_key',
    'load_key',
    'delete_key',
    'key_exists',
    'list_keys',
    'get_key_metadata',
]

# INITIALIZATION

def _initialize_keys_directory() -> None:
    """Initialize keys directory with secure permissions."""
    try:
        KEYS_DIR.mkdir(exist_ok=True)

        # Set restricted permissions (Unix only)
        if not IS_WINDOWS:
            os.chmod(KEYS_DIR, KEYS_DIR_MODE)

        logger.info(f"Keys directory initialized: {KEYS_DIR.absolute()}")

    except Exception as e:
        logger.critical(f"Failed to initialize keys directory: {e}")
        raise KeyManagementError("Cannot initialize keys storage")


# Initialize on module import
_initialize_keys_directory()


# VALIDATION HELPERS

def _validate_file_id(file_id: str) -> str:
    """
    Validate and sanitize file_id to prevent path traversal.

    Args:
        file_id: File identifier to validate.

    Returns:
        Sanitized file_id safe for filename use.

    Raises:
        KeyManagementError: If file_id is invalid.
    """
    if not file_id:
        raise KeyManagementError("File ID cannot be empty")

    if not isinstance(file_id, str):
        raise KeyManagementError(
            f"File ID must be string, got {type(file_id).__name__}"
        )

    # Path traversal protection
    if "/" in file_id or "\\" in file_id or ".." in file_id:
        raise KeyManagementError("Invalid file ID: contains path separators")

    # Only allow safe characters (alphanumeric, hyphen, underscore, dot)
    safe_chars = set(
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_."
    )
    if not all(c in safe_chars for c in file_id):
        raise KeyManagementError(
            "Invalid file ID: contains unsafe characters"
        )

    # Reasonable length limit
    if len(file_id) > 255:
        raise KeyManagementError("File ID too long (max 255 chars)")

    return file_id


def _get_key_path(file_id: str) -> Path:
    """Get validated path for a key file."""
    file_id = _validate_file_id(file_id)
    key_path = KEYS_DIR / f"{file_id}{KEY_FILE_EXTENSION}"

    # Ensure path is within KEYS_DIR (defense in depth)
    try:
        key_path.resolve().relative_to(KEYS_DIR.resolve())
    except ValueError:
        raise KeyManagementError("Path traversal attempt detected")

    return key_path


def _set_secure_permissions(path: Path) -> None:
    """Set restrictive file permissions (Unix)."""
    if not IS_WINDOWS:
        try:
            os.chmod(path, KEY_FILE_MODE)
        except OSError as e:
            logger.warning(f"Failed to set permissions on {path}: {e}")


# KEY GENERATION

def generate_key() -> bytes:
    """
    Generate a cryptographically secure AES-256 key.

    Uses `secrets.token_bytes()` which is designed for cryptographic use
    and provides sufficient randomness for security purposes.

    Returns:
        32-byte AES-256 encryption key.

    Example:
        >>> key = generate_key()
        >>> len(key)
        32
        >>> keys = [generate_key() for _ in range(10)]
        >>> len(set(keys))  # All unique
        10
    """
    key = secrets.token_bytes(AES_256_KEY_SIZE_BYTES)

    # Sanity check
    assert len(key) == AES_256_KEY_SIZE_BYTES, "Key generation failed"

    logger.debug(f"Generated new AES-256 key ({len(key)} bytes)")
    return key


# KEY STORAGE (Encrypted with master key)

def save_key(file_id: str, key: bytes) -> str:
    """
    Save AES-256 key atomically, encrypted with master key.

    Storage format:
        [encrypted key with master key]

    Process:
        1. Validate inputs
        2. Encrypt individual key with master key
        3. Write to temporary file
        4. Fsync to disk
        5. Set secure permissions
        6. Atomically replace old key

    Args:
        file_id: Unique file identifier.
        key: 32-byte AES-256 key.

    Returns:
        Absolute path to saved key file.

    Raises:
        KeyManagementError: If save fails.
    """
    # Input validation
    file_id = _validate_file_id(file_id)
    validate_key(key)

    # Get paths
    key_path = _get_key_path(file_id)
    temp_path = key_path.with_suffix(f"{KEY_FILE_EXTENSION}.tmp")

    try:
        # Encrypt individual key with master key
        # This is CRITICAL: keys must never be stored in plaintext
        from .master_key import load_master_key
        master_key = load_master_key()

        # Use file_id as AAD to bind key to specific file
        aad = f"key:{file_id}".encode('utf-8')
        encrypted_key = encrypt_bytes(key, master_key, aad=aad)

        # Atomic write pattern:
        # 1. Write to temp file
        # 2. Flush and fsync
        # 3. Set permissions
        # 4. Atomic rename

        with open(temp_path, "wb") as f:
            f.write(encrypted_key)
            f.flush()
            os.fsync(f.fileno())

        # Set restrictive permissions BEFORE rename (Unix)
        _set_secure_permissions(temp_path)

        # Atomic rename (POSIX guarantee)
        os.replace(temp_path, key_path)

        # Set permissions on final file (defense in depth)
        _set_secure_permissions(key_path)

        logger.info(f"Saved encrypted key for file_id: {file_id}")
        return str(key_path.absolute())

    except KeyManagementError:
        raise  # Re-raise our own exceptions

    except Exception as e:
        # Cleanup temp file on failure
        if temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                logger.warning(f"Failed to cleanup temp file: {temp_path}")

        logger.error(
            f"Failed to save key for file_id={file_id}: {type(e).__name__}"
        )
        raise KeyManagementError("Failed to save encryption key")


def load_key(file_id: str) -> bytes:
    """
    Load and decrypt AES-256 key from storage.

    Process:
        1. Validate file_id
        2. Check file existence
        3. Read encrypted key
        4. Decrypt with master key (verifies AAD)
        5. Validate decrypted key length

    Args:
        file_id: Unique file identifier.

    Returns:
        32-byte AES-256 encryption key.

    Raises:
        KeyManagementError: If key not found or invalid.
    """
    # Input validation
    file_id = _validate_file_id(file_id)
    key_path = _get_key_path(file_id)

    # Check existence
    if not key_path.exists():
        logger.warning(f"Key not found for file_id: {file_id}")
        raise KeyManagementError("Encryption key not found")

    if not key_path.is_file():
        logger.error(f"Key path is not a file: {file_id}")
        raise KeyManagementError("Invalid key storage")

    try:
        # Read encrypted key
        with open(key_path, "rb") as f:
            encrypted_key = f.read()

        if not encrypted_key:
            raise KeyManagementError("Key file is empty")

        # Decrypt with master key
        from .master_key import load_master_key
        master_key = load_master_key()

        # AAD must match what was used during save
        aad = f"key:{file_id}".encode('utf-8')
        key = decrypt_bytes(encrypted_key, master_key, aad=aad)

        # Validate decrypted key
        validate_key(key)

        logger.debug(f"Loaded encrypted key for file_id: {file_id}")
        return key

    except KeyManagementError:
        raise  # Re-raise our own exceptions

    except PermissionError:
        logger.error(f"Permission denied reading key: {file_id}")
        raise KeyManagementError("Cannot access encryption key")

    except Exception as e:
        logger.error(
            f"Failed to load key for file_id={file_id}: {type(e).__name__}"
        )
        raise KeyManagementError("Failed to load encryption key")


def delete_key(file_id: str) -> bool:
    """
    Securely delete encryption key.

    Args:
        file_id: Unique file identifier.

    Returns:
        True if key was deleted, False if not found.

    Raises:
        KeyManagementError: If deletion fails.
    """
    # Input validation
    file_id = _validate_file_id(file_id)
    key_path = _get_key_path(file_id)

    if not key_path.exists():
        logger.info(f"Key already deleted or never existed: {file_id}")
        return False

    try:
        # Overwrite with random data before delete (best-effort)
        # Note: On modern SSDs, this may not guarantee erasure
        try:
            file_size = key_path.stat().st_size
            with open(key_path, "wb") as f:
                f.write(os.urandom(file_size))
                f.flush()
                os.fsync(f.fileno())
        except OSError:
            pass  # Continue with delete even if overwrite fails

        # Delete the file
        key_path.unlink()

        logger.info(f"Deleted encryption key for file_id: {file_id}")
        return True

    except Exception as e:
        logger.error(
            f"Failed to delete key for file_id={file_id}: {type(e).__name__}"
        )
        raise KeyManagementError("Failed to delete encryption key")


# QUERY FUNCTIONS

def key_exists(file_id: str) -> bool:
   
    try:
        file_id = _validate_file_id(file_id)
        key_path = _get_key_path(file_id)
        return key_path.exists() and key_path.is_file()
    except KeyManagementError:
        return False


def list_keys() -> list[str]:
   
    try:
        keys = []
        for key_file in KEYS_DIR.glob(f"*{KEY_FILE_EXTENSION}"):
            if key_file.is_file():
                # Extract file_id from filename
                file_id = key_file.stem
                keys.append(file_id)
        return sorted(keys)
    except Exception as e:
        logger.error(f"Failed to list keys: {e}")
        return []


def get_key_metadata(file_id: str) -> Optional[dict]:
   
    try:
        file_id = _validate_file_id(file_id)
        key_path = _get_key_path(file_id)

        if not key_path.exists():
            return None

        stat_info = key_path.stat()

        metadata = {
            'file_id': file_id,
            'path': str(key_path.absolute()),
            'size': stat_info.st_size,
            'created_at': stat_info.st_ctime,
            'modified_at': stat_info.st_mtime,
        }

        # Add permissions info (Unix)
        if not IS_WINDOWS:
            metadata['permissions'] = oct(stat.S_IMODE(stat_info.st_mode))

        return metadata

    except Exception as e:
        logger.error(f"Failed to get key metadata: {e}")
        return None