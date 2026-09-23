"""
Central Configuration Loader — TrustShare Security

DB-driven configuration for the entire security module.
Every configurable value comes from the database.
Zero hardcoding — all values from AppConfig table.

Usage:
    from src.security.config_loader import get_config, get_config_int, get_config_json
    
    max_size = get_config_int("MAX_FILE_SIZE", db=db)
    rate_limits = get_config_json("RATE_LIMITS", db=db)

Architecture:
    1. Load from DB (AppConfig table)
    2. Cache in memory (configurable TTL)
    3. Fallback to safe defaults ONLY if DB unavailable
    4. Thread-safe
"""

import os
import json
import time
import logging
from typing import Any, Optional, Dict
from threading import Lock

logger = logging.getLogger(__name__)

# CACHE CONFIGURATION

_config_cache: Dict[str, Any] = {}
_cache_timestamp: float = 0
_cache_lock = Lock()
CACHE_TTL_SECONDS = 300  # Refresh from DB every 5 minutes

# SAFE DEFAULTS (Used ONLY when DB is completely unavailable)
# These are NOT the primary source — DB values always take priority

_SAFE_DEFAULTS = {
    # File Upload
    "MAX_FILE_SIZE": str(100 * 1024 * 1024),  # 100 MB
    "MIN_FILE_SIZE": "1",
    "MAX_FILENAME_LENGTH": "255",
    
    # Encryption
    "ENCRYPTION_ALGORITHM": "AES-256-GCM",
    "ENCRYPTION_VERSION": "1",
    "KEY_SIZE_BYTES": "32",
    "NONCE_SIZE_BYTES": "12",
    
    # Key Rotation
    "KEY_ROTATION_DAYS": "90",
    "KEY_ROTATION_GRACE_PERIOD": "7",
    "MAX_ROTATIONS_PER_BATCH": "100",
    
    # Password Policy
    "PASSWORD_MIN_LENGTH": "8",
    "PASSWORD_MAX_LENGTH": "128",
    "PASSWORD_MIN_SCORE": "60",
    "COMMON_PASSWORDS": json.dumps(["password", "123456", "admin", "qwerty", "letmein"]),
    
    # Rate Limiting
    "RATE_LIMITS": json.dumps({
        "security_health": {"requests": 30, "window_seconds": 60},
        "rotate_keys": {"requests": 5, "window_seconds": 300},
        "validate_password": {"requests": 20, "window_seconds": 60},
        "verify_file": {"requests": 10, "window_seconds": 60},
        "suggest_password": {"requests": 15, "window_seconds": 60},
        "audit_log": {"requests": 20, "window_seconds": 60},
        "performance": {"requests": 30, "window_seconds": 60},
        "default": {"requests": 60, "window_seconds": 60},
    }),
    
    # Storage
    "STORAGE_BACKEND": "local",
    "AWS_S3_BUCKET": "trustshare-files",
    "AWS_S3_REGION": "us-east-1",
    "AWS_S3_PREFIX": "encrypted/",
    
    # MongoDB
    "MONGODB_ENABLED": "true",
    "MONGODB_COLLECTION": "security_activity_logs",
    
    # Monitoring
    "SUSPICIOUS_ACTIVITY_THRESHOLD": "5",
    "SUSPICIOUS_ACTIVITY_WINDOW_HOURS": "24",
    "AUDIT_LOG_RETENTION_DAYS": "365",
    "PERFORMANCE_HISTORY_SIZE": "1000",
    "SLOW_OPERATION_THRESHOLD_MS": "1000",
    
    # Token Lengths (bytes)
    "TOKEN_DEFAULT_LENGTH": "32",
    "TOKEN_SHARE_LENGTH": "32",
    "TOKEN_DOWNLOAD_LENGTH": "48",
    "TOKEN_API_SECRET_LENGTH": "64",
    "TOKEN_SESSION_LENGTH": "48",
    "TOKEN_CSRF_LENGTH": "32",
    "TOKEN_RESET_LENGTH": "32",
    "OTP_LENGTH": "6",
    
    # Token TTL (seconds)
    "TOKEN_DEFAULT_TTL": "3600",
    "TOKEN_SHARE_TTL": str(7 * 24 * 3600),
    "TOKEN_DOWNLOAD_TTL": "300",
    "TOKEN_OTP_TTL": "600",
    "TOKEN_RESET_TTL": "900",
}

__all__ = [
    'get_config',
    'get_config_int',
    'get_config_float',
    'get_config_bool',
    'get_config_json',
    'get_config_list',
    'refresh_config_cache',
    'get_all_configs',
]


# CORE LOADER FUNCTIONS

def _load_all_configs_from_db(db) -> Dict[str, str]:
    """Load ALL configs from DB into cache."""
    try:
        from src.security.models.app_config import AppConfig
        
        rows = db.query(AppConfig).all()
        configs = {}
        for row in rows:
            configs[row.config_key] = row.config_value
        
        logger.debug(f"Loaded {len(configs)} configs from DB")
        return configs
        
    except Exception as e:
        logger.warning(f"Failed to load configs from DB: {e}")
        return {}


def _get_cached_or_load(db=None) -> Dict[str, str]:
    """Get configs from cache or load from DB."""
    global _config_cache, _cache_timestamp
    
    now = time.time()
    
    with _cache_lock:
        # Return cache if fresh
        if _config_cache and (now - _cache_timestamp) < CACHE_TTL_SECONDS:
            return _config_cache
        
        # Try DB
        if db:
            db_configs = _load_all_configs_from_db(db)
            if db_configs:
                _config_cache = db_configs
                _cache_timestamp = now
                return _config_cache
        
        # Return whatever we have (cache or empty)
        return _config_cache


def get_config(key: str, db=None, default: str = None) -> str:
    """
    Get configuration value from DB.
    
    Priority:
        1. DB value (cached)
        2. Provided default
        3. Safe default from _SAFE_DEFAULTS
    
    Args:
        key: Configuration key (e.g., "MAX_FILE_SIZE")
        db: Optional SQLAlchemy session
        default: Optional custom default
        
    Returns:
        Configuration value as string
    """
    # Try cache/DB
    configs = _get_cached_or_load(db)
    
    if key in configs:
        return configs[key]
    
    # Try provided default
    if default is not None:
        return default
    
    # Try safe defaults
    if key in _SAFE_DEFAULTS:
        return _SAFE_DEFAULTS[key]
    
    logger.warning(f"Config key '{key}' not found anywhere")
    return ""


def get_config_int(key: str, db=None, default: int = 0) -> int:
    """Get config value as integer."""
    value = get_config(key, db, str(default))
    try:
        return int(value)
    except (ValueError, TypeError):
        logger.warning(f"Config '{key}' is not a valid integer: {value}")
        return default


def get_config_float(key: str, db=None, default: float = 0.0) -> float:
    """Get config value as float."""
    value = get_config(key, db, str(default))
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def get_config_bool(key: str, db=None, default: bool = False) -> bool:
    """Get config value as boolean."""
    value = get_config(key, db, str(default))
    return value.lower() in ('true', '1', 'yes', 'on')


def get_config_json(key: str, db=None, default=None) -> Any:
    """Get config value parsed as JSON."""
    value = get_config(key, db)
    if not value:
        return default if default is not None else {}
    
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        logger.warning(f"Config '{key}' is not valid JSON: {value[:50]}")
        return default if default is not None else {}


def get_config_list(key: str, db=None, default=None) -> list:
    """Get config value as list (JSON array)."""
    result = get_config_json(key, db, default)
    if isinstance(result, list):
        return result
    return default if default is not None else []


# CACHE MANAGEMENT

def refresh_config_cache(db=None) -> int:
    """
    Force refresh config cache from DB.
    
    Returns:
        Number of configs loaded.
    """
    global _config_cache, _cache_timestamp
    
    with _cache_lock:
        if db:
            _config_cache = _load_all_configs_from_db(db)
            _cache_timestamp = time.time()
            return len(_config_cache)
        
        _config_cache = {}
        _cache_timestamp = 0
        return 0


def get_all_configs(db=None) -> Dict[str, str]:
    """Get all configuration values (for admin display)."""
    configs = _get_cached_or_load(db)
    
    # Merge with safe defaults (show what's missing)
    all_configs = {}
    for key, default in _SAFE_DEFAULTS.items():
        all_configs[key] = {
            "value": configs.get(key, default),
            "source": "database" if key in configs else "default",
            "default": default,
        }
    
    # Add any DB-only configs not in defaults
    for key, value in configs.items():
        if key not in all_configs:
            all_configs[key] = {
                "value": value,
                "source": "database",
                "default": None,
            }
    
    return all_configs