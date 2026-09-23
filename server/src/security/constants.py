"""
Security constants for the TrustShare Encryption & Security module.
"""

# Encryption

AES_KEY_SIZE = 32  # 256 bits
AES_NONCE_SIZE = 12  # AES-GCM recommended nonce size
AES_TAG_SIZE = 16

# File Upload

UPLOAD_CHUNK_SIZE = 64 * 1024  # 64 KB


# Tokens

DEFAULT_TOKEN_LENGTH = 32
SHARE_TOKEN_LENGTH = 48
DOWNLOAD_TOKEN_LENGTH = 64

