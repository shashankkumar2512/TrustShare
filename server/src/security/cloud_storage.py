"""
Cloud Storage Abstraction — TrustShare Security

Storage interface ready for AWS S3 migration.
Currently uses local filesystem.
Switch to S3 by setting STORAGE_BACKEND=s3 in .env.

References:
- PSD: Files stored in AWS S3
- AWS S3 SDK: boto3
"""

import os
import logging
from typing import Optional
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)

__all__ = [
    'StorageBackend',
    'get_storage_backend',
    'get_storage_config',
]


class StorageBackend(str, Enum):
    """Available storage backends."""
    LOCAL = "local"
    AWS_S3 = "s3"


# Current backend (from env)
STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "local")

# AWS S3 configuration (only used if backend = s3)
AWS_S3_CONFIG = {
    "bucket": os.getenv("AWS_S3_BUCKET", "trustshare-files"),
    "region": os.getenv("AWS_REGION", "us-east-1"),
    "prefix": os.getenv("AWS_S3_PREFIX", "encrypted/"),
    "access_key": os.getenv("AWS_ACCESS_KEY_ID"),
    "secret_key": os.getenv("AWS_SECRET_ACCESS_KEY"),
}


def get_storage_backend() -> str:
    """Get current storage backend name."""
    return STORAGE_BACKEND


def get_storage_config() -> dict:
    """
    Get storage configuration (safe — no secrets).
    
    Returns:
        Config dict without sensitive data.
    """
    config = {
        "backend": STORAGE_BACKEND,
        "local": {
            "upload_dir": str(Path("uploads").absolute()),
            "keys_dir": str(Path("keys").absolute()),
        },
    }
    
    if STORAGE_BACKEND == "s3":
        config["s3"] = {
            "bucket": AWS_S3_CONFIG["bucket"],
            "region": AWS_S3_CONFIG["region"],
            "prefix": AWS_S3_CONFIG["prefix"],
            "configured": bool(AWS_S3_CONFIG["access_key"]),
        }
    
    return config


# AWS S3 FUNCTIONS (for future use)

def _get_s3_client():
    """Get AWS S3 client (lazy initialization)."""
    try:
        import boto3
        return boto3.client(
            "s3",
            region_name=AWS_S3_CONFIG["region"],
            aws_access_key_id=AWS_S3_CONFIG["access_key"],
            aws_secret_access_key=AWS_S3_CONFIG["secret_key"],
        )
    except ImportError:
        logger.error("boto3 not installed — install with: pip install boto3")
        return None
    except Exception as e:
        logger.error(f"Failed to create S3 client: {e}")
        return None


def upload_to_s3(filename: str, data: bytes) -> Optional[str]:
    """
    Upload encrypted file to AWS S3.
    
    ⚠️ FUTURE USE — not yet integrated into main flow.
    
    Args:
        filename: Object key in S3.
        data: Encrypted file bytes.
        
    Returns:
        S3 URI or None on failure.
    """
    client = _get_s3_client()
    if not client:
        return None
    
    try:
        key = f"{AWS_S3_CONFIG['prefix']}{filename}"
        
        client.put_object(
            Bucket=AWS_S3_CONFIG["bucket"],
            Key=key,
            Body=data,
            ServerSideEncryption="AES256",
            ContentType="application/octet-stream",
        )
        
        s3_uri = f"s3://{AWS_S3_CONFIG['bucket']}/{key}"
        logger.info(f"Uploaded to S3: {s3_uri}")
        return s3_uri
        
    except Exception as e:
        logger.error(f"S3 upload failed: {e}")
        return None


def download_from_s3(filename: str) -> Optional[bytes]:
    """
    Download encrypted file from AWS S3.
    
    ⚠️ FUTURE USE.
    """
    client = _get_s3_client()
    if not client:
        return None
    
    try:
        key = f"{AWS_S3_CONFIG['prefix']}{filename}"
        
        response = client.get_object(
            Bucket=AWS_S3_CONFIG["bucket"],
            Key=key,
        )
        
        data = response["Body"].read()
        logger.info(f"Downloaded from S3: {key} ({len(data)} bytes)")
        return data
        
    except Exception as e:
        logger.error(f"S3 download failed: {e}")
        return None


def delete_from_s3(filename: str) -> bool:
    """
    Delete file from AWS S3.
    
    ⚠️ FUTURE USE.
    """
    client = _get_s3_client()
    if not client:
        return False
    
    try:
        key = f"{AWS_S3_CONFIG['prefix']}{filename}"
        
        client.delete_object(
            Bucket=AWS_S3_CONFIG["bucket"],
            Key=key,
        )
        
        logger.info(f"Deleted from S3: {key}")
        return True
        
    except Exception as e:
        logger.error(f"S3 delete failed: {e}")
        return False