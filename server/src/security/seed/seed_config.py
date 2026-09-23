"""
Security Configuration Seeder — TrustShare Security

Seeds ALL security configuration into AppConfig table.
Zero hardcoding — everything from database.
"""

import json
from sqlalchemy.orm import Session
from src.security.models.app_config import AppConfig

DEFAULT_CONFIGS = [
    {"config_key": "MAX_FILE_SIZE", "config_value": str(100 * 1024 * 1024), "description": "Maximum upload size in bytes (100 MB)"},
    {"config_key": "MIN_FILE_SIZE", "config_value": "1", "description": "Minimum upload size in bytes"},
    {"config_key": "MAX_FILENAME_LENGTH", "config_value": "255", "description": "Maximum filename character length"},
    {"config_key": "KEY_ROTATION_DAYS", "config_value": "90", "description": "Days between encryption key rotations"},
    {"config_key": "KEY_ROTATION_GRACE_PERIOD", "config_value": "7", "description": "Grace period days before rotation becomes critical"},
    {"config_key": "MAX_ROTATIONS_PER_BATCH", "config_value": "100", "description": "Maximum files to rotate in one batch"},
    {"config_key": "COMMON_PASSWORDS", "config_value": json.dumps(["password","123456","password123","admin","qwerty","letmein","welcome","monkey","dragon","master","iloveyou","abc123","111111","password1","1234567","12345678","12345","1234","123","sunshine","princess","football","shadow","michael","computer","jesus","ninja","mustang","access","batman","trustno1","hello","hunter","buster","soccer","harley","andrew","tigger","jordan","michelle","loveme","banana","asdfgh","asdf","1q2w3e4r","zxcvbnm","qazwsx","1qaz2wsx","abcdef","starwars","letmein123","password12","welcome123","admin123","root","toor","pass","test","guest","user","test123","demo","sample","temp","temp123"]), "description": "Common passwords blocklist (JSON array)"},
    {"config_key": "PASSWORD_MIN_LENGTH", "config_value": "8", "description": "Minimum password length"},
    {"config_key": "PASSWORD_MAX_LENGTH", "config_value": "128", "description": "Maximum password length"},
    {"config_key": "PASSWORD_MIN_SCORE", "config_value": "60", "description": "Minimum password strength score (0-100)"},
    {"config_key": "RATE_LIMITS", "config_value": json.dumps({"security_health":{"requests":30,"window_seconds":60},"rotate_keys":{"requests":5,"window_seconds":300},"validate_password":{"requests":20,"window_seconds":60},"verify_file":{"requests":10,"window_seconds":60},"suggest_password":{"requests":15,"window_seconds":60},"audit_log":{"requests":20,"window_seconds":60},"performance":{"requests":30,"window_seconds":60},"default":{"requests":60,"window_seconds":60}}), "description": "Rate limit configuration per endpoint (JSON)"},
    {"config_key": "ENCRYPTION_ALGORITHM", "config_value": "AES-256-GCM", "description": "Current encryption algorithm"},
    {"config_key": "ENCRYPTION_VERSION", "config_value": "1", "description": "Encryption algorithm version"},
    {"config_key": "NONCE_SIZE_BYTES", "config_value": "12", "description": "GCM nonce size (NIST recommended)"},
    {"config_key": "KEY_SIZE_BYTES", "config_value": "32", "description": "AES-256 key size in bytes"},
    {"config_key": "STORAGE_BACKEND", "config_value": "local", "description": "Storage backend: local or s3"},
    {"config_key": "AWS_S3_BUCKET", "config_value": "trustshare-files", "description": "AWS S3 bucket name"},
    {"config_key": "AWS_S3_REGION", "config_value": "us-east-1", "description": "AWS S3 region"},
    {"config_key": "AWS_S3_PREFIX", "config_value": "encrypted/", "description": "S3 key prefix for encrypted files"},
    {"config_key": "MONGODB_ENABLED", "config_value": "true", "description": "Enable MongoDB for activity logging"},
    {"config_key": "MONGODB_COLLECTION", "config_value": "security_activity_logs", "description": "MongoDB collection name"},
    {"config_key": "SUSPICIOUS_ACTIVITY_THRESHOLD", "config_value": "5", "description": "Unauthorized attempts before CRITICAL"},
    {"config_key": "SUSPICIOUS_ACTIVITY_WINDOW_HOURS", "config_value": "24", "description": "Time window for counting attempts"},
    {"config_key": "AUDIT_LOG_RETENTION_DAYS", "config_value": "365", "description": "Days to retain audit logs"},
    {"config_key": "PERFORMANCE_HISTORY_SIZE", "config_value": "1000", "description": "Max performance operations in memory"},
    {"config_key": "SLOW_OPERATION_THRESHOLD_MS", "config_value": "1000", "description": "Slow operation warning threshold (ms)"},
]


def seed_configs(db: Session):
    """Seed all security configs. Only inserts missing keys."""
    seeded = 0
    for config in DEFAULT_CONFIGS:
        exists = (
            db.query(AppConfig)
            .filter(AppConfig.config_key == config["config_key"])
            .first()
        )
        if not exists:
            db.add(AppConfig(**config))
            seeded += 1

    db.commit()
    print(f"  [OK] Security configs: {seeded} seeded, {len(DEFAULT_CONFIGS)} total defined")