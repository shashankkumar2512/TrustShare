"""
Encryption Algorithm Registry — TrustShare Security

Supports multiple encryption algorithms for forward compatibility.
When upgrading algorithms, old data can still be decrypted.

Current: AES-256-GCM (v1)
Future: Can add AES-256-XTS, ChaCha20-Poly1305, etc.

References:
- NIST SP 800-38D (GCM)
- NIST SP 800-38E (XTS)
- RFC 8439 (ChaCha20-Poly1305)
"""

import logging
from typing import Dict, Optional, Callable
from dataclasses import dataclass

from .exceptions import EncryptionError

logger = logging.getLogger(__name__)

__all__ = [
    'AlgorithmInfo',
    'get_current_algorithm',
    'get_algorithm_info',
    'list_algorithms',
    'CURRENT_VERSION',
]


# ALGORITHM DEFINITIONS

@dataclass
class AlgorithmInfo:
    """Information about an encryption algorithm."""
    version: int
    name: str
    key_size_bits: int
    key_size_bytes: int
    nonce_size_bytes: int
    tag_size_bytes: int
    standard: str
    status: str  # "active", "deprecated", "future"
    description: str


# Algorithm registry
ALGORITHMS: Dict[int, AlgorithmInfo] = {
    1: AlgorithmInfo(
        version=1,
        name="AES-256-GCM",
        key_size_bits=256,
        key_size_bytes=32,
        nonce_size_bytes=12,
        tag_size_bytes=16,
        standard="NIST SP 800-38D",
        status="active",
        description="AES-256 in Galois/Counter Mode. "
                    "Provides authenticated encryption with associated data (AEAD). "
                    "Industry standard for file encryption.",
    ),
    2: AlgorithmInfo(
        version=2,
        name="ChaCha20-Poly1305",
        key_size_bits=256,
        key_size_bytes=32,
        nonce_size_bytes=12,
        tag_size_bytes=16,
        standard="RFC 8439",
        status="future",
        description="ChaCha20 stream cipher with Poly1305 MAC. "
                    "Alternative to AES-GCM, better performance on devices without AES-NI.",
    ),
}

# Current active version
CURRENT_VERSION = 1


# QUERY FUNCTIONS

def get_current_algorithm() -> AlgorithmInfo:
    """Get the currently active encryption algorithm."""
    return ALGORITHMS[CURRENT_VERSION]


def get_algorithm_info(version: int) -> Optional[AlgorithmInfo]:
    """Get info about a specific algorithm version."""
    return ALGORITHMS.get(version)


def list_algorithms() -> list:
    """List all registered algorithms."""
    return [
        {
            "version": algo.version,
            "name": algo.name,
            "key_size_bits": algo.key_size_bits,
            "standard": algo.standard,
            "status": algo.status,
            "description": algo.description,
        }
        for algo in ALGORITHMS.values()
    ]


def is_version_supported(version: int) -> bool:
    """Check if an algorithm version is supported."""
    algo = ALGORITHMS.get(version)
    return algo is not None and algo.status in ("active", "deprecated")