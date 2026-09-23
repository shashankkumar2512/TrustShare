"""
AES-256 Encryption Module — TrustShare Encryption & Security

Industry-grade AES-256-GCM authenticated encryption with:
- Strict key validation (256-bit only)
- Input sanitization
- Secure error handling (no info leaks)
- Associated Authenticated Data (AAD) for context binding
- Comprehensive logging
- Type safety
- Streaming support for large files

References:
- NIST SP 800-38D (GCM specification)
- OWASP Cryptographic Storage Cheat Sheet
- PRD 4.i: AES-256 Encryption
"""

import os
import logging
from typing import Optional, Union
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag

from .exceptions import EncryptionError, DecryptionError
from .performance import track_encryption, track_decryption

# CONSTANTS (NIST-compliant)

# AES-256 requires exactly 32 bytes (256 bits) key
AES_256_KEY_SIZE_BYTES = 32

# NIST SP 800-38D recommends 96-bit (12-byte) nonces for GCM
# Larger nonces are technically allowed but reduce security
# Smaller nonces increase collision risk
GCM_NONCE_SIZE_BYTES = 12

# GCM authentication tag is always 128 bits (16 bytes)
GCM_TAG_SIZE_BYTES = 16

# Minimum ciphertext size: nonce + tag + at least 1 byte
MIN_CIPHERTEXT_SIZE = GCM_NONCE_SIZE_BYTES + GCM_TAG_SIZE_BYTES + 1

# Maximum file size for in-memory encryption (500 MB)
# Larger files should use streaming API
MAX_IN_MEMORY_SIZE = 500 * 1024 * 1024

# Encryption version identifier (for future algorithm migrations)
ENCRYPTION_VERSION = b'\x01'  # AES-256-GCM v1

# Public API
__all__ = [
    'encrypt_bytes',
    'decrypt_bytes',
    'validate_key',
    'is_valid_ciphertext',
    'AES_256_KEY_SIZE_BYTES',
    'GCM_NONCE_SIZE_BYTES',
    'GCM_TAG_SIZE_BYTES',
]

# Setup logger
logger = logging.getLogger(__name__)


# VALIDATION HELPERS

def validate_key(key: bytes) -> None:
    """
    Validate AES-256 encryption key.

    Args:
        key: Encryption key to validate.

    Raises:
        EncryptionError: If key is invalid.
    """
    if key is None:
        raise EncryptionError("Encryption key cannot be None")

    if not isinstance(key, (bytes, bytearray)):
        raise EncryptionError(
            f"Key must be bytes, got {type(key).__name__}"
        )

    if len(key) != AES_256_KEY_SIZE_BYTES:
        raise EncryptionError(
            f"AES-256 requires exactly {AES_256_KEY_SIZE_BYTES}-byte key, "
            f"got {len(key)} bytes"
        )


def _validate_plaintext(data: bytes) -> None:
    """Internal plaintext validation."""
    if data is None:
        raise EncryptionError("Cannot encrypt None data")

    if not isinstance(data, (bytes, bytearray)):
        raise EncryptionError(
            f"Data must be bytes, got {type(data).__name__}"
        )

    if len(data) > MAX_IN_MEMORY_SIZE:
        raise EncryptionError(
            f"File too large for in-memory encryption "
            f"({len(data)} bytes > {MAX_IN_MEMORY_SIZE} bytes). "
            f"Use streaming API for large files."
        )


def _validate_ciphertext(data: bytes) -> None:
    """Internal ciphertext validation."""
    if data is None:
        raise DecryptionError("Cannot decrypt None data")

    if not isinstance(data, (bytes, bytearray)):
        raise DecryptionError(
            f"Data must be bytes, got {type(data).__name__}"
        )

    if len(data) < MIN_CIPHERTEXT_SIZE:
        raise DecryptionError(
            f"Ciphertext too short: {len(data)} bytes "
            f"(minimum {MIN_CIPHERTEXT_SIZE} bytes required)"
        )


def is_valid_ciphertext(data: bytes) -> bool:
    """
    Check if bytes could be valid AES-GCM ciphertext.
    
    Args:
        data: Bytes to check.
        
    Returns:
        True if data has valid ciphertext structure.
    """
    try:
        _validate_ciphertext(data)
        return True
    except DecryptionError:
        return False


# ENCRYPTION FUNCTIONS


@track_encryption
def encrypt_bytes(
    data: bytes,
    key: bytes,
    aad: Optional[bytes] = None,
) -> bytes:
    """
    Encrypt bytes using AES-256-GCM authenticated encryption.

    Format: [12-byte nonce][ciphertext][16-byte auth tag]

    Args:
        data: Plaintext bytes to encrypt.
        key: 32-byte AES-256 encryption key.
        aad: Optional Additional Authenticated Data for context binding.
             Example: f"file:{file_id}:owner:{user_id}".encode()

    Returns:
        Encrypted bytes with nonce prefixed and auth tag appended.

    Raises:
        EncryptionError: If encryption fails for any reason.

    Example:
        >>> key = os.urandom(32)
        >>> plaintext = b"Confidential data"
        >>> ciphertext = encrypt_bytes(plaintext, key)
        >>> len(ciphertext) > len(plaintext)  # nonce + tag added
        True

    Performance:
        - ~1 GB/s on modern hardware (AES-NI)
        - Memory: O(n) where n = len(data)
        - For files > 500MB, use streaming API
    """
    # Input validation (fail fast, secure defaults)
    _validate_plaintext(data)
    validate_key(key)

    if aad is not None and not isinstance(aad, (bytes, bytearray)):
        raise EncryptionError(
            f"AAD must be bytes or None, got {type(aad).__name__}"
        )

    try:
        # Create GCM cipher
        aes = AESGCM(bytes(key))

        # Generate cryptographically secure random nonce
        nonce = os.urandom(GCM_NONCE_SIZE_BYTES)

        # Encrypt with authentication
        ciphertext_with_tag = aes.encrypt(nonce, bytes(data), aad)

        # Log success (debug level, no sensitive data)
        logger.debug(
            f"Encrypted {len(data)} bytes → {len(ciphertext_with_tag)} bytes "
            f"(overhead: {len(ciphertext_with_tag) - len(data)} bytes)"
        )

        # Return: nonce + ciphertext + tag
        return nonce + ciphertext_with_tag

    except (TypeError, ValueError) as e:
        logger.error(f"Encryption input error: {type(e).__name__}")
        raise EncryptionError("Encryption failed: invalid input")

    except MemoryError:
        logger.critical("Encryption failed: insufficient memory")
        raise EncryptionError("Encryption failed: insufficient memory")

    except Exception as e:
        # Log full details internally, return generic error
        logger.critical(
            f"Unexpected encryption failure: {type(e).__name__}",
            exc_info=True,
        )
        raise EncryptionError("Encryption operation failed")


    
@track_decryption
def decrypt_bytes(
    data: bytes,
    key: bytes,
    aad: Optional[bytes] = None,
) -> bytes:

    """
    Decrypt AES-256-GCM encrypted bytes with tamper detection.

    Args:
        data: Encrypted bytes (nonce + ciphertext + tag).
        key: 32-byte AES-256 encryption key.
        aad: Optional Additional Authenticated Data (must match encryption).

    Returns:
        Original plaintext bytes.

    Raises:
        DecryptionError: If decryption fails or data is tampered.

    Security:
        - GCM auth tag verification is automatic
        - Tampered data → InvalidTag → DecryptionError
        - Wrong key → InvalidTag → DecryptionError
        - Wrong AAD → InvalidTag → DecryptionError

    Example:
        >>> ciphertext = encrypt_bytes(b"secret", key)
        >>> plaintext = decrypt_bytes(ciphertext, key)
        >>> plaintext == b"secret"
        True
    """
    # Input validation
    _validate_ciphertext(data)
    validate_key(key)

    if aad is not None and not isinstance(aad, (bytes, bytearray)):
        raise DecryptionError(
            f"AAD must be bytes or None, got {type(aad).__name__}"
        )

    try:
        # Extract nonce (first 12 bytes)
        nonce = bytes(data[:GCM_NONCE_SIZE_BYTES])

        # Extract ciphertext + auth tag (remaining bytes)
        ciphertext_with_tag = bytes(data[GCM_NONCE_SIZE_BYTES:])

        # Create GCM cipher
        aes = AESGCM(bytes(key))

        # Decrypt and verify (auth tag checked automatically)
        plaintext = aes.decrypt(nonce, ciphertext_with_tag, aad)

        # Log success (debug level)
        logger.debug(
            f"Decrypted {len(data)} bytes → {len(plaintext)} bytes"
        )

        return plaintext

    except InvalidTag:
        # Specific case: authentication failed (tampering detected)
        logger.warning("Decryption failed: authentication tag invalid")
        raise DecryptionError(
            "Decryption failed: data may be corrupted or tampered"
        )

    except (TypeError, ValueError) as e:
        logger.error(f"Decryption input error: {type(e).__name__}")
        raise DecryptionError("Decryption failed: invalid input")

    except MemoryError:
        logger.critical("Decryption failed: insufficient memory")
        raise DecryptionError("Decryption failed: insufficient memory")

    except Exception as e:
        # Log details internally, return generic error
        logger.critical(
            f"Unexpected decryption failure: {type(e).__name__}",
            exc_info=True,
        )
        raise DecryptionError("Decryption operation failed")


# HELPER FUNCTIONS

def generate_aad(**kwargs) -> bytes:
    """
    Generate Additional Authenticated Data from keyword arguments.
    
    AAD binds encrypted data to specific context (file_id, owner, etc.)
    preventing "ciphertext relocation" attacks.
    
    Args:
        **kwargs: Context data (file_id, owner_id, timestamp, etc.)
        
    Returns:
        Deterministic bytes representation of context.
        
    Example:
        >>> aad = generate_aad(file_id=123, owner_id=456)
        >>> encrypted = encrypt_bytes(data, key, aad=aad)
        >>> # Decryption must use SAME aad
        >>> decrypted = decrypt_bytes(encrypted, key, aad=aad)
    """
    # Sort keys for deterministic output
    sorted_items = sorted(kwargs.items())
    aad_str = "|".join(f"{k}={v}" for k, v in sorted_items)
    return aad_str.encode('utf-8')