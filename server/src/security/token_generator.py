"""
Secure Token Generation Module — TrustShare Encryption & Security

Industry-grade cryptographically secure token generation with:
- Multiple token types (share, download, API, session)
- Configurable lengths per use case
- URL-safe encoding
- Token validation utilities
- HMAC-based signed tokens
- Time-limited token support
- Rate limiting helpers

References:
- NIST SP 800-90A (Random Number Generation)
- OWASP Session Management Cheat Sheet
- RFC 4648 (Base64/Base32 encoding)
- PRD 4.ix: Secure Token Generation
"""

import os
import hmac
import time
import secrets
import string
import logging
import hashlib
import base64
from typing import Optional, Tuple
from datetime import datetime, timezone, timedelta

from .exceptions import KeyManagementError
from src.security.config_loader import get_config_int

# CONFIGURATION

def _token_length(key: str, default: int, db=None) -> int:
    return get_config_int(key, db, default)
# Token lengths (in bytes for token_bytes, chars for random_string)
DEFAULT_TOKEN_LENGTH_BYTES = 32           # 256-bit
SHARE_TOKEN_LENGTH_BYTES = 32             # 256-bit (share links)
DOWNLOAD_TOKEN_LENGTH_BYTES = 48          # 384-bit (download URLs)
API_SECRET_LENGTH_BYTES = 64              # 512-bit (API secrets)
SESSION_TOKEN_LENGTH_BYTES = 48           # 384-bit (session IDs)
CSRF_TOKEN_LENGTH_BYTES = 32              # 256-bit (CSRF protection)
OTP_LENGTH = 6                            # 6-digit OTP
RESET_TOKEN_LENGTH_BYTES = 32             # Password reset tokens

# Character sets for different token types
ALPHANUMERIC = string.ascii_letters + string.digits
NUMERIC_ONLY = string.digits
URL_SAFE_CHARS = string.ascii_letters + string.digits + "-_"
HEX_CHARS = string.hexdigits.lower()[:16]  # 0-9, a-f

# Token expiration defaults (seconds)
DEFAULT_TOKEN_TTL = 3600                  # 1 hour
SHARE_TOKEN_TTL = 7 * 24 * 3600           # 7 days
DOWNLOAD_TOKEN_TTL = 300                  # 5 minutes
OTP_TTL = 600                             # 10 minutes
RESET_TOKEN_TTL = 900                     # 15 minutes

# Rate limiting defaults
DEFAULT_RATE_LIMIT = 10                   # attempts
DEFAULT_RATE_WINDOW = 60                  # seconds

# Setup logger
logger = logging.getLogger(__name__)

# Public API
__all__ = [
    'generate_token',
    'generate_share_token',
    'generate_download_token',
    'generate_api_secret',
    'generate_session_token',
    'generate_csrf_token',
    'generate_otp',
    'generate_reset_token',
    'generate_signed_token',
    'verify_signed_token',
    'validate_token_format',
    'compare_tokens',
    'is_token_expired',
    'DEFAULT_TOKEN_LENGTH_BYTES',
    'SHARE_TOKEN_TTL',
]


# CORE TOKEN GENERATION (Random)

def generate_token(
    length_bytes: int = DEFAULT_TOKEN_LENGTH_BYTES,
    url_safe: bool = True,
) -> str:
    """
    Generate a cryptographically secure random token.
    
    Uses `secrets.token_urlsafe()` or `secrets.token_hex()` which are
    designed for security-sensitive purposes.
    
    Args:
        length_bytes: Length in bytes (final string will be longer due to encoding).
        url_safe: If True, use URL-safe characters (default).
                  If False, use hex encoding.
        
    Returns:
        Secure random token string.
        
    Example:
        >>> token = generate_token()  # 43 chars URL-safe
        >>> hex_token = generate_token(url_safe=False)  # 64 chars hex
    """
    if length_bytes < 16:
        raise KeyManagementError(
            f"Token length too short (min 16 bytes for security)"
        )
    
    if length_bytes > 256:
        raise KeyManagementError(
            f"Token length too long (max 256 bytes)"
        )
    
    try:
        if url_safe:
            # URL-safe base64 encoding
            return secrets.token_urlsafe(length_bytes)
        else:
            # Hexadecimal encoding
            return secrets.token_hex(length_bytes)
    except Exception as e:
        logger.error(f"Token generation failed: {type(e).__name__}")
        raise KeyManagementError("Failed to generate secure token")


def generate_alphanumeric_token(length: int = 32) -> str:
    """
    Generate token with only alphanumeric characters.
    
    Useful when you need predictable character set (e.g., typing manually).
    
    Args:
        length: Number of characters.
        
    Returns:
        Alphanumeric token string.
    """
    if length < 8:
        raise KeyManagementError("Token too short (min 8 chars)")
    
    if length > 128:
        raise KeyManagementError("Token too long (max 128 chars)")
    
    return ''.join(secrets.choice(ALPHANUMERIC) for _ in range(length))


# SPECIALIZED TOKEN TYPES

def generate_share_token() -> str:
    """
    Generate secure token for file sharing links.
    
    Uses 256-bit (32 bytes) random data, URL-safe encoding.
    Format: ~43 URL-safe characters
    
    Returns:
        Share link token.
        
    Example:
        >>> token = generate_share_token()
        >>> len(token)
        43
        >>> # Use in URL: https://app.com/share/{token}
    """
    return generate_token(SHARE_TOKEN_LENGTH_BYTES, url_safe=True)


def generate_download_token() -> str:
    """
    Generate secure token for time-limited download URLs.
    
    Uses 384-bit (48 bytes) random data for extra security since
    download tokens may grant temporary anonymous access.
    
    Returns:
        Download authorization token.
    """
    return generate_token(DOWNLOAD_TOKEN_LENGTH_BYTES, url_safe=True)


def generate_api_secret() -> str:
    """
    Generate secure API secret key.
    
    Uses 512-bit (64 bytes) hex-encoded for maximum security.
    
    Returns:
        API secret string.
        
    Example:
        >>> secret = generate_api_secret()
        >>> len(secret)
        128  # hex encoding doubles length
    """
    return generate_token(API_SECRET_LENGTH_BYTES, url_safe=False)


def generate_session_token() -> str:
    """
    Generate secure session token.
    
    Uses 384-bit (48 bytes) URL-safe encoding.
    
    Returns:
        Session token.
    """
    return generate_token(SESSION_TOKEN_LENGTH_BYTES, url_safe=True)


def generate_csrf_token() -> str:
    """
    Generate CSRF protection token.
    
    Uses 256-bit (32 bytes) URL-safe encoding.
    
    Returns:
        CSRF token.
    """
    return generate_token(CSRF_TOKEN_LENGTH_BYTES, url_safe=True)


def generate_otp(length: int = OTP_LENGTH) -> str:
    """
    Generate One-Time Password (OTP).
    
    Uses cryptographically secure random digits.
    
    Args:
        length: Number of digits (default 6).
        
    Returns:
        Numeric OTP string.
        
    Example:
        >>> otp = generate_otp()
        >>> len(otp)
        6
        >>> otp.isdigit()
        True
    """
    if length < 4:
        raise KeyManagementError("OTP too short (min 4 digits)")
    
    if length > 10:
        raise KeyManagementError("OTP too long (max 10 digits)")
    
    return ''.join(secrets.choice(NUMERIC_ONLY) for _ in range(length))


def generate_reset_token() -> str:
    """
    Generate password reset token.
    
    Uses 256-bit URL-safe encoding for password reset links.
    
    Returns:
        Reset token string.
    """
    return generate_token(RESET_TOKEN_LENGTH_BYTES, url_safe=True)


# SIGNED TOKENS (HMAC-based with expiration)

def generate_signed_token(
    payload: str,
    secret_key: bytes,
    ttl_seconds: int = DEFAULT_TOKEN_TTL,
) -> str:
    """
    Generate signed token with expiration.
    
    Format: base64(payload:timestamp:signature)
    
    This creates a token that:
    - Contains data (payload)
    - Has an expiration timestamp
    - Is signed with HMAC-SHA256
    - Cannot be forged without the secret key
    
    Args:
        payload: Data to include in token (e.g., user_id, file_id).
        secret_key: 32-byte secret key for HMAC signing.
        ttl_seconds: Time-to-live in seconds.
        
    Returns:
        Signed token string (URL-safe base64).
        
    Example:
        >>> secret = os.urandom(32)
        >>> token = generate_signed_token("user:123", secret, ttl_seconds=300)
        >>> # Later, verify:
        >>> data = verify_signed_token(token, secret)
        >>> data['payload']
        'user:123'
    """
    if not payload:
        raise KeyManagementError("Payload cannot be empty")
    
    if not secret_key or len(secret_key) < 32:
        raise KeyManagementError("Secret key must be at least 32 bytes")
    
    if ttl_seconds < 1:
        raise KeyManagementError("TTL must be positive")
    
    try:
        # Timestamp when token expires
        expiry_time = int(time.time()) + ttl_seconds
        
        # Create signing string
        signing_data = f"{payload}:{expiry_time}".encode('utf-8')
        
        # HMAC-SHA256 signature
        signature = hmac.new(
            secret_key,
            signing_data,
            hashlib.sha256
        ).digest()
        
        # Combine payload:timestamp:signature
        token_data = signing_data + b":" + signature
        
        # URL-safe base64 encoding
        token = base64.urlsafe_b64encode(token_data).decode('utf-8').rstrip('=')
        
        return token
        
    except Exception as e:
        logger.error(f"Signed token generation failed: {type(e).__name__}")
        raise KeyManagementError("Failed to generate signed token")


def verify_signed_token(
    token: str,
    secret_key: bytes,
) -> dict:
    """
    Verify and parse signed token.
    
    Args:
        token: Signed token to verify.
        secret_key: Same secret key used for signing.
        
    Returns:
        Dict with:
            - valid: bool
            - expired: bool
            - payload: str (if valid)
            - expiry: int (unix timestamp)
            - error: str (if invalid)
        
    Example:
        >>> result = verify_signed_token(token, secret)
        >>> if result['valid'] and not result['expired']:
        ...     user_id = result['payload']
    """
    if not token:
        return {
            'valid': False,
            'expired': False,
            'error': 'Empty token',
        }
    
    if not secret_key or len(secret_key) < 32:
        return {
            'valid': False,
            'expired': False,
            'error': 'Invalid secret key',
        }
    
    try:
        # Decode from URL-safe base64
        # Add padding if needed
        padding = 4 - (len(token) % 4)
        if padding != 4:
            token_padded = token + ('=' * padding)
        else:
            token_padded = token
        
        token_data = base64.urlsafe_b64decode(token_padded)
        
        # Split components (payload:timestamp:signature)
        # Signature is last 32 bytes (SHA-256 output)
        if len(token_data) < 33:
            return {
                'valid': False,
                'expired': False,
                'error': 'Token too short',
            }
        
        signing_part = token_data[:-32]
        received_signature = token_data[-32:]
        
        # Verify signature (timing-safe)
        expected_signature = hmac.new(
            secret_key,
            signing_part[:-1] if signing_part.endswith(b':') else signing_part,
            hashlib.sha256
        ).digest()
        
        # Re-parse to get exact signing data
        parts = signing_part.rstrip(b':').split(b':')
        if len(parts) < 2:
            return {
                'valid': False,
                'expired': False,
                'error': 'Invalid token format',
            }
        
        payload = b':'.join(parts[:-1]).decode('utf-8')
        expiry_time = int(parts[-1])
        
        # Re-compute expected signature
        expected_data = f"{payload}:{expiry_time}".encode('utf-8')
        expected_signature = hmac.new(
            secret_key,
            expected_data,
            hashlib.sha256
        ).digest()
        
        # Timing-safe comparison
        if not hmac.compare_digest(received_signature, expected_signature):
            return {
                'valid': False,
                'expired': False,
                'error': 'Invalid signature',
            }
        
        # Check expiration
        current_time = int(time.time())
        is_expired = current_time > expiry_time
        
        return {
            'valid': True,
            'expired': is_expired,
            'payload': payload,
            'expiry': expiry_time,
            'remaining_seconds': max(0, expiry_time - current_time),
        }
        
    except (ValueError, base64.binascii.Error) as e:
        return {
            'valid': False,
            'expired': False,
            'error': f'Invalid token encoding',
        }
    
    except Exception as e:
        logger.error(f"Token verification failed: {type(e).__name__}")
        return {
            'valid': False,
            'expired': False,
            'error': 'Token verification failed',
        }


# TOKEN VALIDATION UTILITIES

def validate_token_format(
    token: str,
    min_length: int = 16,
    max_length: int = 128,
    allowed_chars: Optional[str] = None,
) -> bool:
    """
    Validate token format without checking if it exists.
    
    Args:
        token: Token to validate.
        min_length: Minimum acceptable length.
        max_length: Maximum acceptable length.
        allowed_chars: Optional set of allowed characters.
        
    Returns:
        True if token has valid format.
    """
    if not token or not isinstance(token, str):
        return False
    
    if len(token) < min_length or len(token) > max_length:
        return False
    
    if allowed_chars and not all(c in allowed_chars for c in token):
        return False
    
    return True


def is_url_safe_token(token: str) -> bool:
    """Check if token uses only URL-safe characters."""
    return validate_token_format(token, allowed_chars=URL_SAFE_CHARS)


def is_hex_token(token: str) -> bool:
    """Check if token is valid hex."""
    return validate_token_format(token, allowed_chars=HEX_CHARS)


def is_numeric_token(token: str) -> bool:
    """Check if token contains only digits (OTP-like)."""
    return validate_token_format(token, allowed_chars=NUMERIC_ONLY)


def compare_tokens(token1: str, token2: str) -> bool:
    """
    Timing-safe comparison of two tokens.
    
    Use this instead of == to prevent timing attacks.
    
    Args:
        token1: First token.
        token2: Second token.
        
    Returns:
        True if tokens match.
    """
    if not token1 or not token2:
        return False
    
    if not isinstance(token1, str) or not isinstance(token2, str):
        return False
    
    # Timing-safe comparison
    return hmac.compare_digest(token1.encode(), token2.encode())


# EXPIRATION HELPERS

def is_token_expired(created_at: datetime, ttl_seconds: int) -> bool:
    """
    Check if a token has expired based on creation time.
    
    Args:
        created_at: When token was created (timezone-aware).
        ttl_seconds: Token's time-to-live in seconds.
        
    Returns:
        True if token has expired.
        
    Example:
        >>> from datetime import datetime, timezone
        >>> created = datetime.now(timezone.utc)
        >>> is_token_expired(created, 3600)  # 1 hour TTL
        False
    """
    if not created_at:
        return True
    
    # Ensure timezone-aware
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    
    now = datetime.now(timezone.utc)
    age_seconds = (now - created_at).total_seconds()
    
    return age_seconds > ttl_seconds


def get_expiration_time(ttl_seconds: int) -> datetime:
    """
    Calculate expiration datetime.
    
    Args:
        ttl_seconds: Time-to-live in seconds.
        
    Returns:
        Timezone-aware datetime when token expires.
    """
    return datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)


# TOKEN METADATA

def get_token_metadata(token: str) -> dict:
    """
    Get metadata about a token (without decoding signed tokens).
    
    Args:
        token: Token to analyze.
        
    Returns:
        Dict with token metadata.
    """
    if not token:
        return {'valid': False, 'error': 'Empty token'}
    
    metadata = {
        'valid': True,
        'length': len(token),
        'is_url_safe': is_url_safe_token(token),
        'is_hex': is_hex_token(token),
        'is_numeric': is_numeric_token(token),
        'estimated_entropy_bits': len(token) * 5.95,  # ~5.95 bits per char for base64
    }
    
    # Estimate security level
    if metadata['estimated_entropy_bits'] >= 256:
        metadata['security_level'] = 'Very High (256+ bits)'
    elif metadata['estimated_entropy_bits'] >= 128:
        metadata['security_level'] = 'High (128+ bits)'
    elif metadata['estimated_entropy_bits'] >= 80:
        metadata['security_level'] = 'Medium (80+ bits)'
    else:
        metadata['security_level'] = 'Low (<80 bits) - Not recommended'
    
    return metadata


# CLI HELPER

def print_token_examples() -> None:
    """
    Print example tokens for reference.
    
    Useful for developers to see what different tokens look like.
    """
    print("\n" + "=" * 70)
    print("🔐 TRUSTSHARE TOKEN GENERATOR — Examples")
    print("=" * 70)
    
    print(f"\n📎 Share Token (43 chars, URL-safe):")
    print(f"   {generate_share_token()}")
    
    print(f"\n⬇️  Download Token (64 chars, URL-safe):")
    print(f"   {generate_download_token()}")
    
    print(f"\n🔑 API Secret (128 chars, hex):")
    print(f"   {generate_api_secret()[:64]}...")
    
    print(f"\n🎫 Session Token (64 chars, URL-safe):")
    print(f"   {generate_session_token()}")
    
    print(f"\n🛡️  CSRF Token (43 chars, URL-safe):")
    print(f"   {generate_csrf_token()}")
    
    print(f"\n🔢 OTP (6 digits):")
    print(f"   {generate_otp()}")
    
    print(f"\n🔄 Password Reset Token (43 chars):")
    print(f"   {generate_reset_token()}")
    
    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    # Allow running as script to see examples
    print_token_examples()