"""
Custom exceptions for the Encryption & Security module.
"""


class EncryptionError(Exception):
    """Raised when file encryption fails."""
    pass


class DecryptionError(Exception):
    """Raised when file decryption fails."""
    pass


class IntegrityError(Exception):
    """Raised when file integrity verification fails."""
    pass


class KeyManagementError(Exception):
    """Raised when key generation or retrieval fails."""
    pass