"""
Hashing Module — TrustShare Encryption & Security

Industry-grade file hashing and integrity verification with:
- SHA-256 (primary algorithm)
- Timing-safe hash comparison (prevents timing attacks)
- Chunked hashing (memory efficient for large files)
- Multiple hash algorithms support
- Both file-based and bytes-based hashing
- Streaming support

References:
- FIPS 180-4 (SHA-256 specification)
- NIST SP 800-107 (Recommendation for Hash Algorithms)
- OWASP Cryptographic Storage Cheat Sheet
- PRD: SHA-256 integrity verification
"""

import hashlib
import hmac
import logging
from pathlib import Path
from typing import Union, BinaryIO, Optional

from .exceptions import IntegrityError

# CONFIGURATION

# Chunk size for reading large files (64 KB balances speed and memory)
CHUNK_SIZE = 64 * 1024

# SHA-256 produces 32-byte (256-bit) hashes
# Hex representation: 64 characters
SHA256_HEX_LENGTH = 64
SHA256_BYTE_LENGTH = 32

# Supported hash algorithms
SUPPORTED_ALGORITHMS = {
    "sha256": (hashlib.sha256, SHA256_HEX_LENGTH),
    "sha384": (hashlib.sha384, 96),
    "sha512": (hashlib.sha512, 128),
    "sha3_256": (hashlib.sha3_256, 64),
    "blake2b": (hashlib.blake2b, 128),
}

# Setup logger
logger = logging.getLogger(__name__)

# Public API
__all__ = [
    'calculate_sha256',
    'calculate_sha256_bytes',
    'calculate_hash_stream',
    'verify_sha256',
    'verify_hash',
    'compare_hashes',
    'SHA256_HEX_LENGTH',
    'SUPPORTED_ALGORITHMS',
]


# VALIDATION HELPERS

def _validate_hash_format(hash_string: str, expected_length: int = SHA256_HEX_LENGTH) -> None:
    """Validate hash string format."""
    if not hash_string:
        raise IntegrityError("Hash cannot be empty")
    
    if not isinstance(hash_string, str):
        raise IntegrityError(
            f"Hash must be string, got {type(hash_string).__name__}"
        )
    
    if len(hash_string) != expected_length:
        raise IntegrityError(
            f"Invalid hash length: {len(hash_string)} "
            f"(expected {expected_length})"
        )
    
    if not all(c in '0123456789abcdefABCDEF' for c in hash_string):
        raise IntegrityError("Hash contains invalid hex characters")


def _validate_file_path(file_path: Union[str, Path]) -> Path:
    """Validate and convert file path."""
    if not file_path:
        raise IntegrityError("File path cannot be empty")
    
    path = Path(file_path) if isinstance(file_path, str) else file_path
    
    if not path.exists():
        raise IntegrityError(f"File not found: {path}")
    
    if not path.is_file():
        raise IntegrityError(f"Path is not a file: {path}")
    
    return path


# FILE HASHING

def calculate_sha256(file_path: Union[str, Path]) -> str:
    """
    Calculate SHA-256 hash of a file using chunked reading.
    
    Memory efficient: Reads file in 64KB chunks instead of loading
    entire file into memory. Suitable for files of any size.
    
    Args:
        file_path: Path to file (string or Path object).
        
    Returns:
        Hexadecimal SHA-256 hash (64 characters).
        
    Raises:
        IntegrityError: If file not found or read fails.
        
    Example:
        >>> hash = calculate_sha256("/path/to/file.pdf")
        >>> len(hash)
        64
    """
    path = _validate_file_path(file_path)
    
    try:
        sha256 = hashlib.sha256()
        
        with open(path, "rb") as file:
            while chunk := file.read(CHUNK_SIZE):
                sha256.update(chunk)
        
        hash_value = sha256.hexdigest()
        logger.debug(f"Calculated SHA-256 for {path.name}: {hash_value[:16]}...")
        return hash_value
        
    except PermissionError:
        logger.error(f"Permission denied: {path}")
        raise IntegrityError("Cannot read file for hashing")
    
    except OSError as e:
        logger.error(f"IO error hashing {path}: {e}")
        raise IntegrityError("Failed to read file for hashing")
    
    except Exception as e:
        logger.error(f"Unexpected error hashing {path}: {type(e).__name__}")
        raise IntegrityError("Hashing operation failed")


def calculate_sha256_bytes(data: bytes) -> str:
    """
    Calculate SHA-256 hash of bytes in memory.
    
    Args:
        data: Bytes to hash.
        
    Returns:
        Hexadecimal SHA-256 hash.
        
    Example:
        >>> hash = calculate_sha256_bytes(b"Hello, World!")
        >>> len(hash)
        64
    """
    if data is None:
        raise IntegrityError("Cannot hash None")
    
    if not isinstance(data, (bytes, bytearray)):
        raise IntegrityError(
            f"Data must be bytes, got {type(data).__name__}"
        )
    
    try:
        return hashlib.sha256(bytes(data)).hexdigest()
    except Exception as e:
        logger.error(f"Failed to hash bytes: {type(e).__name__}")
        raise IntegrityError("Hashing operation failed")


def calculate_hash_stream(stream: BinaryIO, algorithm: str = "sha256") -> str:
    """
    Calculate hash from a file stream.
    
    Args:
        stream: Binary file stream (opened with 'rb').
        algorithm: Hash algorithm name (sha256, sha512, etc.).
        
    Returns:
        Hexadecimal hash string.
        
    Example:
        >>> with open("file.pdf", "rb") as f:
        ...     hash = calculate_hash_stream(f)
    """
    if not stream:
        raise IntegrityError("Stream cannot be None")
    
    if algorithm not in SUPPORTED_ALGORITHMS:
        raise IntegrityError(
            f"Unsupported algorithm: {algorithm}. "
            f"Supported: {list(SUPPORTED_ALGORITHMS.keys())}"
        )
    
    hash_func, _ = SUPPORTED_ALGORITHMS[algorithm]
    
    try:
        hasher = hash_func()
        
        while chunk := stream.read(CHUNK_SIZE):
            hasher.update(chunk)
        
        return hasher.hexdigest()
        
    except Exception as e:
        logger.error(f"Stream hashing failed: {type(e).__name__}")
        raise IntegrityError("Stream hashing failed")


# HASH VERIFICATION (Timing-Safe)

def verify_sha256(
    file_path: Union[str, Path],
    expected_hash: str,
) -> bool:
    """
    Verify file integrity using SHA-256 hash.
    
    Uses timing-safe comparison to prevent timing attacks.
    
    Args:
        file_path: Path to file.
        expected_hash: Expected SHA-256 hex hash.
        
    Returns:
        True if hashes match, False otherwise.
        
    Raises:
        IntegrityError: If validation fails.
        
    Example:
        >>> stored_hash = "abc123..."  # from database
        >>> is_valid = verify_sha256("/path/to/file", stored_hash)
        >>> if not is_valid:
        ...     print("File may be tampered!")
    """
    # Validate inputs
    _validate_hash_format(expected_hash)
    
    try:
        # Calculate actual hash
        actual_hash = calculate_sha256(file_path)
        
        # Use timing-safe comparison to prevent timing attacks
        return hmac.compare_digest(
            actual_hash.lower(),
            expected_hash.lower()
        )
        
    except IntegrityError:
        raise
    except Exception as e:
        logger.error(f"Hash verification failed: {type(e).__name__}")
        raise IntegrityError("Hash verification failed")


def verify_hash(
    file_path: Union[str, Path],
    expected_hash: str,
    algorithm: str = "sha256",
) -> bool:
    """
    Verify file with any supported hash algorithm.
    
    Args:
        file_path: Path to file.
        expected_hash: Expected hash.
        algorithm: Hash algorithm to use.
        
    Returns:
        True if hashes match.
    """
    if algorithm not in SUPPORTED_ALGORITHMS:
        raise IntegrityError(f"Unsupported algorithm: {algorithm}")
    
    _, expected_length = SUPPORTED_ALGORITHMS[algorithm]
    _validate_hash_format(expected_hash, expected_length)
    
    path = _validate_file_path(file_path)
    
    try:
        with open(path, "rb") as f:
            actual_hash = calculate_hash_stream(f, algorithm)
        
        return hmac.compare_digest(
            actual_hash.lower(),
            expected_hash.lower()
        )
        
    except IntegrityError:
        raise
    except Exception as e:
        logger.error(f"Verification failed: {type(e).__name__}")
        raise IntegrityError("Hash verification failed")


def compare_hashes(hash1: str, hash2: str) -> bool:
    """
    Timing-safe comparison of two hash strings.
    
    Use this instead of == to prevent timing attacks.
    
    Args:
        hash1: First hash.
        hash2: Second hash.
        
    Returns:
        True if hashes match.
        
    Example:
        >>> compare_hashes("abc123", "abc123")
        True
        >>> compare_hashes("abc123", "def456")
        False
    """
    if not hash1 or not hash2:
        return False
    
    if not isinstance(hash1, str) or not isinstance(hash2, str):
        return False
    
    # Use HMAC's timing-safe comparison
    return hmac.compare_digest(hash1.lower(), hash2.lower())


# UTILITY FUNCTIONS

def is_valid_sha256_hash(hash_string: str) -> bool:
    """
    Check if string is a valid SHA-256 hex hash.
    
    Args:
        hash_string: String to validate.
        
    Returns:
        True if valid SHA-256 hash format.
    """
    try:
        _validate_hash_format(hash_string)
        return True
    except IntegrityError:
        return False


def get_file_hash_metadata(file_path: Union[str, Path]) -> dict:
    """
    Get comprehensive hash metadata for a file.
    
    Args:
        file_path: Path to file.
        
    Returns:
        Dict with hashes and metadata.
    """
    path = _validate_file_path(file_path)
    
    try:
        with open(path, "rb") as f:
            data = f.read()
        
        return {
            "filename": path.name,
            "size_bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "sha512": hashlib.sha512(data).hexdigest(),
            "sha3_256": hashlib.sha3_256(data).hexdigest(),
        }
    except Exception as e:
        logger.error(f"Failed to get hash metadata: {e}")
        raise IntegrityError("Failed to compute hash metadata")