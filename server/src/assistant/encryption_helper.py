"""
Assistant Encryption Helper — TrustShare AI Assistant

Provides encryption/decryption for config secrets (like API keys) stored
in the assistant_config table.

Uses the existing master_key.py infrastructure for consistency with
the rest of the encryption module.

Encryption format:
- Encrypted values are stored in DB with prefix "enc_v1:" followed by
  base64-encoded ciphertext (nonce + ciphertext + auth tag)
- This makes it easy to detect encrypted vs plain values
- Version prefix supports future format upgrades
"""

import base64
import logging
from typing import Optional

from src.security.encryption import encrypt_bytes, decrypt_bytes
from src.security.master_key import load_master_key
from src.security.exceptions import EncryptionError, DecryptionError

logger = logging.getLogger(__name__)

ENCRYPTED_PREFIX = "enc_v1:"


def is_encrypted(value: Optional[str]) -> bool:
    if not value or not isinstance(value, str):
        return False
    return value.startswith(ENCRYPTED_PREFIX)


def encrypt_config_value(plain_value: str) -> str:

    if not plain_value:
        raise EncryptionError("Cannot encrypt empty value")

    if is_encrypted(plain_value):
        logger.debug("Value already encrypted, returning as-is")
        return plain_value

    try:
        master_key = load_master_key()
        plain_bytes = plain_value.encode("utf-8")

        aad = b"assistant_config_secret"
        encrypted_bytes = encrypt_bytes(plain_bytes, master_key, aad=aad)

        b64 = base64.b64encode(encrypted_bytes).decode("ascii")

        return f"{ENCRYPTED_PREFIX}{b64}"

    except Exception as e:
        logger.error(f"Config encryption failed: {type(e).__name__}")
        raise EncryptionError("Failed to encrypt config value")


def decrypt_config_value(encrypted_value: Optional[str]) -> Optional[str]:

    if encrypted_value is None:
        return None

    if not isinstance(encrypted_value, str):
        return encrypted_value

    if not is_encrypted(encrypted_value):
        return encrypted_value

    try:
        b64_part = encrypted_value[len(ENCRYPTED_PREFIX) :]
        encrypted_bytes = base64.b64decode(b64_part)

        master_key = load_master_key()
        aad = b"assistant_config_secret"

        plain_bytes = decrypt_bytes(encrypted_bytes, master_key, aad=aad)
        return plain_bytes.decode("utf-8")

    except Exception as e:
        logger.error(f"Config decryption failed: {type(e).__name__}")
        raise DecryptionError("Failed to decrypt config value")


def mask_secret(value: Optional[str], show_last: int = 4) -> str:

    if not value:
        return "Not configured"

    try:
        if is_encrypted(value):
            plain = decrypt_config_value(value)
            if not plain:
                return "Not configured"
            value = plain
    except Exception:
        return "•••••• (encrypted)"

    if len(value) <= show_last:
        return "•" * len(value)

    return "•" * (len(value) - show_last) + value[-show_last:]
