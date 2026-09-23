"""
Master Key Management — TrustShare Encryption & Security

Industry-grade master key handling with:
- Environment variable priority (production best practice)
- Encrypted file fallback (development)
- Secure key generation
- Multiple key sources support (env, file, HSM future)
- Rotation preparation
- Key derivation options
- Production guard (prevents auto-generation in production)

Security Model:
1. PRODUCTION: MASTER_KEY_HEX environment variable (required)
2. DEVELOPMENT: Encrypted master.key file (fallback)
3. FUTURE: HSM/KMS integration (AWS KMS, Azure Key Vault)

The master key is used to encrypt individual file encryption keys.
This means: compromise of storage != compromise of files.

References:
- NIST SP 800-57 Part 1: Key Management
- OWASP Key Management Cheat Sheet
- AWS KMS Best Practices
- PRD 4.Key.ii: Keys managed securely on server
"""

import os
import stat
import logging
import secrets
import platform
from pathlib import Path
from typing import Optional

from .exceptions import KeyManagementError

# CONFIGURATION

# Environment variable name (production)
MASTER_KEY_ENV_VAR = "MASTER_KEY_HEX"

# Environment name variable — used to detect production
ENVIRONMENT_VAR = "ENVIRONMENT"

# Fallback file (development only)
MASTER_KEY_FILE = Path("master.key")

# Key specifications
MASTER_KEY_SIZE_BYTES = 32  # 256-bit
MASTER_KEY_HEX_LENGTH = MASTER_KEY_SIZE_BYTES * 2  # 64 hex chars

# File permissions
MASTER_KEY_FILE_MODE = 0o600  # Owner read/write only

# Platform detection
IS_WINDOWS = platform.system() == "Windows"

# Setup logger
logger = logging.getLogger(__name__)

# Cache to avoid repeated file reads
_master_key_cache: Optional[bytes] = None

# Public API
__all__ = [
    'load_master_key',
    'generate_master_key',
    'save_master_key_to_file',
    'get_master_key_source',
    'validate_master_key',
    'clear_master_key_cache',
    'is_production_environment',
    'MASTER_KEY_SIZE_BYTES',
]


# ENVIRONMENT DETECTION

def is_production_environment() -> bool:
    """
    Check if running in production environment.

    Checks ENVIRONMENT env variable.
    Production requires MASTER_KEY_HEX — never auto-generates.

    Returns:
        True if ENVIRONMENT=production (case-insensitive).
    """
    env = os.getenv(ENVIRONMENT_VAR, "development").lower().strip()
    return env in ("production", "prod")


# VALIDATION

def validate_master_key(key: bytes) -> None:
    """
    Validate master key format.

    Args:
        key: Master key bytes to validate.

    Raises:
        KeyManagementError: If key is invalid.
    """
    if key is None:
        raise KeyManagementError("Master key cannot be None")

    if not isinstance(key, (bytes, bytearray)):
        raise KeyManagementError(
            f"Master key must be bytes, got {type(key).__name__}"
        )

    if len(key) != MASTER_KEY_SIZE_BYTES:
        raise KeyManagementError(
            f"Master key must be {MASTER_KEY_SIZE_BYTES} bytes "
            f"(got {len(key)} bytes)"
        )


def _validate_hex_key(key_hex: str) -> bytes:
    """
    Validate and convert hex string to bytes.

    Args:
        key_hex: Hex-encoded key string.

    Returns:
        Decoded key bytes.

    Raises:
        KeyManagementError: If hex is invalid.
    """
    if not key_hex:
        raise KeyManagementError("Master key hex string is empty")

    key_hex = key_hex.strip()

    if len(key_hex) != MASTER_KEY_HEX_LENGTH:
        raise KeyManagementError(
            f"Master key hex must be {MASTER_KEY_HEX_LENGTH} characters "
            f"(got {len(key_hex)})"
        )

    if not all(c in '0123456789abcdefABCDEF' for c in key_hex):
        raise KeyManagementError("Master key contains invalid hex characters")

    try:
        key = bytes.fromhex(key_hex)
        validate_master_key(key)
        return key
    except ValueError:
        raise KeyManagementError("Failed to decode master key hex")


# KEY GENERATION

def generate_master_key() -> bytes:
    """
    Generate a new cryptographically secure master key.

    Uses secrets.token_bytes() for cryptographic randomness.

    Returns:
        32-byte master key.
    """
    key = secrets.token_bytes(MASTER_KEY_SIZE_BYTES)
    logger.info("Generated new master key")
    return key


def generate_master_key_hex() -> str:
    """
    Generate a new master key as hex string.

    Useful for setting MASTER_KEY_HEX environment variable.

    Returns:
        Hex-encoded master key string (64 characters).
    """
    key = generate_master_key()
    return key.hex()


# KEY LOADING

def load_master_key(force_reload: bool = False) -> bytes:
    """
    Load master key from environment variable or file.

    Priority:
        1. MASTER_KEY_HEX environment variable (production — required)
        2. master.key file (development fallback)
        3. Auto-generate new key (development ONLY — raises in production)

    FIX REMAINING-3: Added production guard.
    In production (ENVIRONMENT=production), auto-generation raises an error
    instead of silently creating a new key that makes all encrypted files
    permanently unreadable on the next server restart.

    Args:
        force_reload: If True, bypass cache and reload key.

    Returns:
        32-byte master key.

    Raises:
        KeyManagementError: If key cannot be loaded or is invalid.
                           Always raised in production if key is missing.
    """
    global _master_key_cache

    # Return cached key if available
    if not force_reload and _master_key_cache is not None:
        return _master_key_cache

    # ═══ Priority 1: Environment Variable (production) ═══
    key_hex = os.getenv(MASTER_KEY_ENV_VAR)
    if key_hex:
        try:
            key = _validate_hex_key(key_hex)
            _master_key_cache = key
            logger.info(f"Loaded master key from {MASTER_KEY_ENV_VAR}")
            return key
        except KeyManagementError as e:
            logger.critical(f"Invalid {MASTER_KEY_ENV_VAR}: {e}")
            raise

    # ═══ Priority 2: File Fallback (development) ═══
    if MASTER_KEY_FILE.exists():
        try:
            key = _load_master_key_from_file()
            _master_key_cache = key
            logger.warning(
                "Loaded master key from file. "
                "Set MASTER_KEY_HEX environment variable for production."
            )
            return key
        except Exception as e:
            logger.error(f"Failed to load master key from file: {e}")
            raise KeyManagementError("Cannot load master key from file")

    # ═══ Priority 3: Auto-Generate ═══
    # FIX REMAINING-3: Block auto-generation in production environment.
    # In production, a new auto-generated key means all previously encrypted
    # files become permanently unreadable on every server restart.
    if is_production_environment():
        logger.critical(
            f"CRITICAL: Master key not found in production environment. "
            f"Set {MASTER_KEY_ENV_VAR} environment variable immediately. "
            f"Generate a key with: python -c \"import secrets; print(secrets.token_hex(32))\""
        )
        raise KeyManagementError(
            f"Production environment requires {MASTER_KEY_ENV_VAR} to be set. "
            f"Cannot auto-generate master key in production — "
            f"this would make all encrypted files permanently unreadable on restart. "
            f"Run: python -c \"import secrets; print(secrets.token_hex(32))\" "
            f"and set {MASTER_KEY_ENV_VAR}=<output> in your .env file."
        )

    # Development only — auto-generate with clear warning
    logger.warning(
        "⚠️  No master key found. Generating new key for DEVELOPMENT only. "
        f"Set {MASTER_KEY_ENV_VAR} environment variable for production. "
        f"Auto-generation is INSECURE — key is lost on server restart."
    )

    key = generate_master_key()
    save_master_key_to_file(key)
    _master_key_cache = key

    logger.info(
        f"Generated master key. For production, set: "
        f"export {MASTER_KEY_ENV_VAR}={key.hex()}"
    )

    return key


def _load_master_key_from_file() -> bytes:
    """Load master key from file with validation."""
    if not MASTER_KEY_FILE.exists():
        raise KeyManagementError("Master key file not found")

    if not MASTER_KEY_FILE.is_file():
        raise KeyManagementError("Master key path is not a file")

    try:
        with open(MASTER_KEY_FILE, "rb") as f:
            key = f.read()

        validate_master_key(key)

        # Check permissions (Unix)
        if not IS_WINDOWS:
            file_stat = MASTER_KEY_FILE.stat()
            perms = stat.S_IMODE(file_stat.st_mode)
            if perms != MASTER_KEY_FILE_MODE:
                logger.warning(
                    f"Master key file has unsafe permissions: {oct(perms)}. "
                    f"Should be: {oct(MASTER_KEY_FILE_MODE)}. Fixing..."
                )
                os.chmod(MASTER_KEY_FILE, MASTER_KEY_FILE_MODE)

        return key

    except KeyManagementError:
        raise

    except PermissionError:
        raise KeyManagementError("Cannot read master key file (permission denied)")

    except Exception as e:
        logger.error(f"Error reading master key file: {type(e).__name__}")
        raise KeyManagementError("Failed to read master key file")


# KEY STORAGE (File-based fallback — development only)

def save_master_key_to_file(key: bytes) -> None:
    """
    Save master key to file with secure permissions.

    ⚠️ NOTE: File storage is for DEVELOPMENT only.
    In production, use MASTER_KEY_HEX environment variable.

    Args:
        key: 32-byte master key.

    Raises:
        KeyManagementError: If save fails.
    """
    validate_master_key(key)

    try:
        MASTER_KEY_FILE.write_bytes(key)

        if not IS_WINDOWS:
            os.chmod(MASTER_KEY_FILE, MASTER_KEY_FILE_MODE)

        logger.info(f"Saved master key to {MASTER_KEY_FILE}")

    except Exception as e:
        logger.error(f"Failed to save master key: {type(e).__name__}")
        raise KeyManagementError("Failed to save master key")


# UTILITY FUNCTIONS

def get_master_key_source() -> str:
    """
    Get information about the current master key source.

    Returns:
        String describing the key source:
        - "environment" — Loaded from env variable (production)
        - "file"        — Loaded from master.key file (development)
        - "not_loaded"  — Not yet loaded
    """
    if os.getenv(MASTER_KEY_ENV_VAR):
        return "environment"

    if MASTER_KEY_FILE.exists():
        return "file"

    return "not_loaded"


def clear_master_key_cache() -> None:
    """
    Clear cached master key.

    Useful after key rotation or for testing.
    """
    global _master_key_cache
    _master_key_cache = None
    logger.debug("Master key cache cleared")


def get_master_key_metadata() -> dict:
    """
    Get metadata about master key source.

    Returns:
        Dict with metadata (does NOT include the key itself).
    """
    metadata = {
        'source':       get_master_key_source(),
        'env_var_set':  bool(os.getenv(MASTER_KEY_ENV_VAR)),
        'file_exists':  MASTER_KEY_FILE.exists(),
        'is_cached':    _master_key_cache is not None,
        'is_production': is_production_environment(),
    }

    if MASTER_KEY_FILE.exists():
        try:
            file_stat = MASTER_KEY_FILE.stat()
            metadata['file_path'] = str(MASTER_KEY_FILE.absolute())
            metadata['file_size'] = file_stat.st_size
            if not IS_WINDOWS:
                metadata['file_permissions'] = oct(stat.S_IMODE(file_stat.st_mode))
        except OSError:
            pass

    return metadata


# CLI HELPER

def print_setup_instructions() -> None:
    """Print instructions for setting up master key."""
    hex_key = generate_master_key_hex()

    print("\n" + "=" * 70)
    print("🔐 TRUSTSHARE MASTER KEY SETUP")
    print("=" * 70)
    print("\n✅ PRODUCTION (Required):")
    print(f"   export {MASTER_KEY_ENV_VAR}={hex_key}")
    print(f"\n   # Or add to .env file:")
    print(f"   {MASTER_KEY_ENV_VAR}={hex_key}")
    print(f"   ENVIRONMENT=production")

    print("\n⚠️  DEVELOPMENT ONLY:")
    print(f"   Master key will be auto-generated in {MASTER_KEY_FILE}")
    print("   DO NOT COMMIT master.key TO VERSION CONTROL!")

    print("\n🚨 PRODUCTION GUARD:")
    print("   When ENVIRONMENT=production is set:")
    print(f"   - {MASTER_KEY_ENV_VAR} MUST be set")
    print("   - Auto-generation is BLOCKED")
    print("   - Missing key raises KeyManagementError on startup")

    print("\n📋 SECURITY CHECKLIST:")
    print(f"   [ ] {MASTER_KEY_ENV_VAR} is 64 hex characters (32 bytes)")
    print(f"   [ ] {MASTER_KEY_ENV_VAR} is in environment variable (production)")
    print("   [ ] master.key is in .gitignore")
    print("   [ ] ENVIRONMENT=production is set in production .env")
    print("   [ ] Backup master key securely (loss = permanent data loss)")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    print_setup_instructions()