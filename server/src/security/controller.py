"""
Security API Controller — TrustShare Encryption & Security

Industry-grade API endpoints for security monitoring and management.
Includes health checks, metrics, rotation, validation, and audit.

Endpoints:
- GET  /api/security/health              → Security health status
- GET  /api/security/rotation-status     → Key rotation health
- GET  /api/security/metrics             → Security dashboard metrics
- POST /api/security/rotate-keys         → Batch rotate keys (admin)
- POST /api/security/verify-file/{id}    → Verify file integrity
- GET  /api/security/audit-log           → Recent security events (admin)
- GET  /api/security/info                → Module capabilities
- GET  /api/security/performance         → Encryption performance metrics
- POST /api/security/performance/reset   → Reset metrics (admin)
- POST /api/security/validate-password   → Password strength checker
- GET  /api/security/suggest-password    → Password suggestion
- GET  /api/security/algorithms          → Encryption algorithm info
- GET  /api/security/storage-backends    → Storage backend status
- GET  /api/security/rate-limits         → Rate limit configuration

References:
- PRD 4: Security Features monitoring
- OWASP: Security Logging and Monitoring
"""

import hashlib
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from src.database.core import get_db
from src.auth.dependencies import get_current_user, require_admin
from src.entities.user import User
from src.entities.file import File
from src.entities.audit_log import AuditLog

from src.security.key_rotation import (
    get_rotation_status,
    rotate_expired_keys,
    rotate_all_keys,
    should_rotate,
    days_until_rotation,
    KEY_ROTATION_DAYS,
)
from src.security.master_key import get_master_key_metadata
from src.security.secure_storage import get_storage_stats
from src.security.hashing import calculate_sha256, verify_sha256
from src.security.secure_storage import load_encrypted_file
from src.security.key_manager import load_key, list_keys
from src.security.encryption import decrypt_bytes
from src.security.rate_limiter import check_rate_limit, get_rate_limits_config
from src.security.config_loader import get_all_configs, refresh_config_cache
from src.security.exceptions import (
    EncryptionError,
    DecryptionError,
    IntegrityError,
    KeyManagementError,
)
from src.security.performance import (
    get_performance_metrics,
    reset_metrics,
)
from src.security.password_validator import (
    validate_password,
    suggest_strong_password,
    PasswordStrength,
)
from src.security.algorithm_registry import (
    get_current_algorithm,
    list_algorithms,
    CURRENT_VERSION,
)
from src.security.activity_logger import (
    is_mongodb_available,
    get_activity_stats,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# RATE LIMITING HELPER

def _check_rate(request: Request, user: User, endpoint: str, db: Session):
    """Check rate limit and raise 429 if exceeded."""
    client_id = str(user.id) if user else "anonymous"
    result = check_rate_limit(client_id, endpoint, db)
    
    if not result["allowed"]:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Try again in {result['reset_in']}s",
            headers={
                "Retry-After": str(int(result["reset_in"])),
                "X-RateLimit-Limit": str(result["limit"]),
                "X-RateLimit-Remaining": "0",
            }
        )
    return result


# RESPONSE MODELS

class SecurityHealthResponse(BaseModel):
    """Overall security health status."""
    status: str
    score: int
    encryption_healthy: bool
    keys_healthy: bool
    storage_healthy: bool
    master_key_source: str
    total_encrypted_files: int
    keys_needing_rotation: int
    security_events_24h: int
    failed_operations_24h: int
    checked_at: str


class RotationStatusResponse(BaseModel):
    """Key rotation status details."""
    health_status: str
    health_score: int
    total_encrypted_files: int
    needs_rotation: int
    in_grace_period: int
    fresh_keys: int
    oldest_key_age_days: Optional[int]
    rotation_policy_days: int
    recommendation: str


class RotationResultResponse(BaseModel):
    """Result of batch key rotation."""
    success: bool
    total_checked: int
    successfully_rotated: int
    failed_rotations: int
    duration_seconds: float
    errors: List[dict]


class FileVerificationResponse(BaseModel):
    """File integrity verification result."""
    file_id: int
    filename: str
    is_valid: bool
    stored_hash: str
    calculated_hash: Optional[str]
    file_size: int
    encrypted: bool
    verified_at: str
    error: Optional[str] = None


class SecurityMetricsResponse(BaseModel):
    """Security metrics for dashboard."""
    total_files_encrypted: int
    total_encryption_keys: int
    keys_needing_rotation: int
    security_events_1h: int
    security_events_24h: int
    security_events_7d: int
    failed_logins_24h: int
    unauthorized_attempts_24h: int
    master_key_source: str
    storage_used_mb: float
    encryption_algorithm: str
    key_algorithm: str


class PasswordValidationRequest(BaseModel):
    """Request to validate a password."""
    password: str
    username: Optional[str] = None
    email: Optional[str] = None


class PasswordValidationApiResponse(BaseModel):
    """API response for password validation."""
    is_valid: bool
    score: int
    strength: str
    issues: List[str]
    suggestions: List[str]
    estimated_crack_time: str


# HEALTH CHECK ENDPOINTS

@router.get("/health", response_model=SecurityHealthResponse)
def security_health_check(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get overall security health status.
    
    Returns comprehensive security health check including:
    - Encryption status
    - Key management health
    - Storage health
    - Recent security events
    """
    _check_rate(request, current_user, "security_health", db)
    
    try:
        now = datetime.now(timezone.utc)
        yesterday = now - timedelta(hours=24)
        
        rotation = get_rotation_status(db)
        keys_healthy = rotation.get('health_score', 0) >= 75
        
        master_key_meta = get_master_key_metadata()
        master_key_source = master_key_meta.get('source', 'unknown')
        
        try:
            storage = get_storage_stats()
            storage_healthy = storage.get('disk_usage_percent', 100) < 90
        except Exception:
            storage_healthy = True
        
        encryption_healthy = True
        
        security_events = (
            db.query(AuditLog)
            .filter(
                AuditLog.level.in_(['warning', 'error', 'critical']),
                AuditLog.created_at >= yesterday,
            ).count()
        )
        
        failed_operations = (
            db.query(AuditLog)
            .filter(
                AuditLog.action.in_([
                    'UNAUTHORIZED_ACCESS',
                    'DECRYPTION_FAILED',
                    'INTEGRITY_FAILURE',
                    'KEY_ROTATION_FAILED',
                ]),
                AuditLog.created_at >= yesterday,
            ).count()
        )
        
        total_encrypted = (
            db.query(File)
            .filter(
                File.is_deleted == False,
                File.encrypted == True,
            ).count()
        )
        
        score = 100
        if not keys_healthy:
            score -= 25
        if master_key_source != 'environment':
            score -= 15
        if not storage_healthy:
            score -= 10
        if failed_operations > 10:
            score -= 20
        elif failed_operations > 5:
            score -= 10
        if security_events > 50:
            score -= 15
        elif security_events > 20:
            score -= 5
        
        if score >= 90:
            status_label = "excellent"
        elif score >= 75:
            status_label = "good"
        elif score >= 60:
            status_label = "fair"
        else:
            status_label = "poor"
        
        return SecurityHealthResponse(
            status=status_label,
            score=score,
            encryption_healthy=encryption_healthy,
            keys_healthy=keys_healthy,
            storage_healthy=storage_healthy,
            master_key_source=master_key_source,
            total_encrypted_files=total_encrypted,
            keys_needing_rotation=rotation.get('needs_rotation', 0),
            security_events_24h=security_events,
            failed_operations_24h=failed_operations,
            checked_at=now.isoformat(),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Security health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check security health"
        )


@router.get("/rotation-status", response_model=RotationStatusResponse)
def get_key_rotation_status(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get key rotation status and health."""
    _check_rate(request, current_user, "security_health", db)
    
    try:
        status_data = get_rotation_status(db)
        
        if 'error' in status_data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=status_data['error']
            )
        
        return RotationStatusResponse(
            health_status=status_data['health_status'],
            health_score=status_data['health_score'],
            total_encrypted_files=status_data['total_encrypted_files'],
            needs_rotation=status_data['needs_rotation'],
            in_grace_period=status_data['in_grace_period'],
            fresh_keys=status_data['fresh_keys'],
            oldest_key_age_days=status_data.get('oldest_key_age_days'),
            rotation_policy_days=status_data['rotation_policy_days'],
            recommendation=status_data['recommendation'],
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get rotation status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve rotation status"
        )


# SECURITY METRICS ENDPOINT

@router.get("/metrics", response_model=SecurityMetricsResponse)
def get_security_metrics(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get security metrics for dashboard display."""
    _check_rate(request, current_user, "security_health", db)
    
    try:
        now = datetime.now(timezone.utc)
        last_hour = now - timedelta(hours=1)
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)
        
        total_encrypted = (
            db.query(File)
            .filter(File.is_deleted == False, File.encrypted == True)
            .count()
        )
        
        try:
            total_keys = len(list_keys())
        except Exception:
            total_keys = 0
        
        rotation = get_rotation_status(db)
        keys_needing_rotation = rotation.get('needs_rotation', 0)
        
        events_1h = (
            db.query(AuditLog)
            .filter(
                AuditLog.level.in_(['warning', 'error', 'critical']),
                AuditLog.created_at >= last_hour,
            ).count()
        )
        
        events_24h = (
            db.query(AuditLog)
            .filter(
                AuditLog.level.in_(['warning', 'error', 'critical']),
                AuditLog.created_at >= last_24h,
            ).count()
        )
        
        events_7d = (
            db.query(AuditLog)
            .filter(
                AuditLog.level.in_(['warning', 'error', 'critical']),
                AuditLog.created_at >= last_7d,
            ).count()
        )
        
        from src.analytics.models.analytics_event import AnalyticsEvent
        from src.analytics.constants import AnalyticsEventType, AnalyticsEventStatus
        
        failed_logins = (
            db.query(AnalyticsEvent)
            .filter(
                AnalyticsEvent.event_type == AnalyticsEventType.LOGIN,
                AnalyticsEvent.status == AnalyticsEventStatus.FAILED,
                AnalyticsEvent.created_at >= last_24h,
            ).count()
        )
        
        unauthorized = (
            db.query(AuditLog)
            .filter(
                AuditLog.action == 'UNAUTHORIZED_ACCESS',
                AuditLog.created_at >= last_24h,
            ).count()
        )
        
        try:
            storage = get_storage_stats()
            storage_mb = storage.get('total_size_mb', 0)
        except Exception:
            storage_mb = 0
        
        master_key_meta = get_master_key_metadata()
        
        algo = get_current_algorithm()
        return SecurityMetricsResponse(
            total_files_encrypted=total_encrypted,
            total_encryption_keys=total_keys,
            keys_needing_rotation=keys_needing_rotation,
            security_events_1h=events_1h,
            security_events_24h=events_24h,
            security_events_7d=events_7d,
            failed_logins_24h=failed_logins,
            unauthorized_attempts_24h=unauthorized,
            master_key_source=master_key_meta.get('source', 'unknown'),
            storage_used_mb=storage_mb,
            encryption_algorithm=algo.name,
            key_algorithm=f"{algo.name} ({algo.key_size_bits}-bit keys)",
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get security metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve security metrics"
        )


# ADMIN ENDPOINTS

@router.post("/rotate-keys", response_model=RotationResultResponse)
def batch_rotate_keys(
    request: Request,
    dry_run: bool = Query(False, description="Preview without rotating"),
    max_batch: int = Query(100, ge=1, le=1000, description="Max files to rotate"),
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    """
    Trigger batch key rotation for expired keys.
    ⚠️ ADMIN ONLY
    """
    _check_rate(request, admin_user, "rotate_keys", db)
    
    try:
        logger.info(
            f"Admin {admin_user.id} triggered batch rotation "
            f"(dry_run={dry_run}, max_batch={max_batch})"
        )
        
        result = rotate_expired_keys(
            db=db,
            max_batch=max_batch,
            dry_run=dry_run,
        )
        
        return RotationResultResponse(
            success=True,
            total_checked=result['total_checked'],
            successfully_rotated=result['successfully_rotated'],
            failed_rotations=result['failed_rotations'],
            duration_seconds=result['duration_seconds'],
            errors=result['errors'][:10],
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch rotation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch rotation failed"
        )


@router.post("/verify-file/{file_id}", response_model=FileVerificationResponse)
def verify_file_integrity(
    file_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Verify integrity of an encrypted file.
    Available to file owner or admin.
    """
    _check_rate(request, current_user, "verify_file", db)
    
    try:
        file = (
            db.query(File)
            .filter(File.id == file_id, File.is_deleted == False)
            .first()
        )
        
        if not file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        if file.owner_id != current_user.id and current_user.role != 'admin':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to verify this file"
            )
        
        try:
            encrypted_bytes = load_encrypted_file(file.stored_name)
            
            if file.encrypted:
                aes_key = load_key(file.stored_name)
                decrypted_bytes = decrypt_bytes(encrypted_bytes, aes_key)
            else:
                decrypted_bytes = encrypted_bytes
            
            calculated_hash = hashlib.sha256(decrypted_bytes).hexdigest()
            is_valid = calculated_hash == file.hash_sha256
            
            audit = AuditLog(
                user_id=current_user.id,
                action="INTEGRITY_CHECK" if is_valid else "INTEGRITY_FAILURE",
                resource_type="file",
                resource_id=file.id,
                resource_name=file.original_name,
                level="info" if is_valid else "critical",
            )
            db.add(audit)
            db.commit()
            
            return FileVerificationResponse(
                file_id=file.id,
                filename=file.original_name,
                is_valid=is_valid,
                stored_hash=file.hash_sha256,
                calculated_hash=calculated_hash,
                file_size=file.size,
                encrypted=file.encrypted,
                verified_at=datetime.now(timezone.utc).isoformat(),
                error=None if is_valid else "Hash mismatch - file may be corrupted",
            )
            
        except (KeyManagementError, DecryptionError) as e:
            logger.error(f"Verification failed for file {file_id}: {e}")
            return FileVerificationResponse(
                file_id=file.id,
                filename=file.original_name,
                is_valid=False,
                stored_hash=file.hash_sha256,
                calculated_hash=None,
                file_size=file.size,
                encrypted=file.encrypted,
                verified_at=datetime.now(timezone.utc).isoformat(),
                error=f"Verification failed: {type(e).__name__}",
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Verification failed"
        )


@router.get("/audit-log")
def get_security_audit_log(
    request: Request,
    limit: int = Query(50, ge=1, le=500),
    level: Optional[str] = Query(None, description="Filter by level"),
    action: Optional[str] = Query(None, description="Filter by action"),
    hours: int = Query(24, ge=1, le=168, description="Hours to look back"),
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    """
    Get recent security audit log entries.
    ⚠️ ADMIN ONLY
    """
    _check_rate(request, admin_user, "audit_log", db)
    
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        query = db.query(AuditLog).filter(AuditLog.created_at >= cutoff)
        
        if level:
            query = query.filter(AuditLog.level == level)
        if action:
            query = query.filter(AuditLog.action == action)
        
        logs = (
            query.order_by(AuditLog.created_at.desc())
            .limit(limit)
            .all()
        )
        
        return {
            "total": len(logs),
            "hours_back": hours,
            "logs": [
                {
                    "id": log.id,
                    "user_id": log.user_id,
                    "action": log.action,
                    "resource_type": log.resource_type,
                    "resource_id": log.resource_id,
                    "resource_name": log.resource_name,
                    "level": log.level,
                    "created_at": log.created_at.isoformat() if log.created_at else None,
                }
                for log in logs
            ],
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch audit log: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve audit log"
        )


# INFORMATION ENDPOINT

@router.get("/info")
def get_security_module_info(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get information about the security module."""
    from src.security.key_rotation import _get_rotation_days
    rotation_days = _get_rotation_days(db)

    return {
        "module": "TrustShare Encryption & Security",
        "version": "2.0.0",
        "capabilities": {
            "encryption_algorithm": "AES-256-GCM",
            "key_size_bits": 256,
            "nonce_size_bytes": 12,
            "hash_algorithm": "SHA-256",
            "hash_algorithms_supported": [
                "SHA-256", "SHA-384", "SHA-512", "SHA3-256", "BLAKE2b"
            ],
            "key_rotation_policy_days": rotation_days,
            "master_key_encrypted_storage": True,
            "atomic_writes": True,
            "path_traversal_protection": True,
            "magic_bytes_verification": True,
            "streaming_support": True,
            "signed_tokens": True,
        },
        "standards_compliance": {
            "AES_256_GCM": "NIST SP 800-38D",
            "SHA_256": "FIPS 180-4",
            "Key_Management": "NIST SP 800-57",
            "JWT": "RFC 7519",
        },
        "features": {
            "unique_key_per_file": True,
            "master_key_encryption": True,
            "path_traversal_protection": True,
            "magic_bytes_verification": True,
            "timing_safe_comparison": True,
            "atomic_file_operations": True,
            "streaming_support": True,
            "automatic_key_rotation": True,
            "batch_rotation": True,
            "integrity_verification": True,
            "audit_logging": True,
            "suspicious_activity_detection": True,
            "password_strength_validation": True,
            "performance_metrics": True,
            "rate_limiting": True,
            "algorithm_versioning": True,
            "mongodb_activity_logging": True,
            "aws_s3_ready": True,
        },
    }


# PERFORMANCE ENDPOINTS

@router.get("/performance")
def get_encryption_performance(
    request: Request,
    operation: Optional[str] = Query(None, description="Filter by operation type"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get encryption performance metrics."""
    _check_rate(request, current_user, "performance", db)
    
    try:
        metrics = get_performance_metrics(operation)
        return {
            "status": "success",
            "metrics": metrics,
            "captured_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve performance metrics"
        )


@router.post("/performance/reset")
def reset_performance_metrics(
    admin_user: User = Depends(require_admin),
):
    """Reset all performance metrics. ⚠️ ADMIN ONLY"""
    try:
        reset_metrics()
        logger.info(f"Admin {admin_user.id} reset performance metrics")
        return {
            "status": "success",
            "message": "Performance metrics reset",
            "reset_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        logger.error(f"Failed to reset metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset metrics"
        )


# PASSWORD VALIDATION ENDPOINTS

@router.post("/validate-password", response_model=PasswordValidationApiResponse)
def validate_password_strength(
    request_data: PasswordValidationRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Validate password strength.
    
    Checks length, character variety, common passwords, sequential patterns,
    repeated characters, username/email inclusion.
    """
    _check_rate(request, current_user, "validate_password", db)
    
    try:
        result = validate_password(
            password=request_data.password,
            username=request_data.username,
            email=request_data.email,
            db=db,
        )
        
        return PasswordValidationApiResponse(
            is_valid=result.is_valid,
            score=result.score,
            strength=result.strength.value,
            issues=result.issues,
            suggestions=result.suggestions,
            estimated_crack_time=result.estimated_crack_time,
        )
    except Exception as e:
        logger.error(f"Password validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password validation failed"
        )


@router.get("/suggest-password")
def get_strong_password_suggestion(
    request: Request,
    length: int = Query(16, ge=8, le=128, description="Password length"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a suggested strong password."""
    _check_rate(request, current_user, "suggest_password", db)
    
    try:
        password = suggest_strong_password(length)
        return {
            "password": password,
            "length": len(password),
            "strength": "very_strong",
        }
    except Exception as e:
        logger.error(f"Password suggestion failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to suggest password"
        )


# ALGORITHM & STORAGE ENDPOINTS

@router.get("/algorithms")
def get_encryption_algorithms(
    current_user: User = Depends(get_current_user),
):
    """Get supported encryption algorithms."""
    current = get_current_algorithm()
    return {
        "current_version": CURRENT_VERSION,
        "current_algorithm": {
            "name": current.name,
            "key_size_bits": current.key_size_bits,
            "standard": current.standard,
            "status": current.status,
        },
        "all_algorithms": list_algorithms(),
    }


@router.get("/storage-backends")
def get_storage_backend_status(
    current_user: User = Depends(get_current_user),
):
    """Get status of all storage backends (PostgreSQL, MongoDB, File Storage)."""
    try:
        storage = get_storage_stats()
        mongo_stats = get_activity_stats()
        
        return {
            "postgresql": {
                "status": "connected",
                "primary": True,
                "purpose": "File metadata, user data, audit logs",
            },
            "mongodb": {
                "status": "connected" if is_mongodb_available() else "unavailable",
                "primary": False,
                "purpose": "Security activity logs (per PSD)",
                "stats": mongo_stats,
                "fallback": "PostgreSQL audit_log table",
            },
            "file_storage": {
                "backend": "local_filesystem",
                "ready_for": "AWS S3 migration",
                "stats": storage,
            },
        }
    except Exception as e:
        logger.error(f"Storage backend check failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to check storage backends"
        )


@router.get("/rate-limits")
def get_rate_limit_config(
    current_user: User = Depends(get_current_user),
):
    """Get current rate limit configuration."""
    return {
        "limits": get_rate_limits_config(),
        "source": "default (override via DB: RATE_LIMITS config key)",
    }

@router.get("/configs")
def get_security_configs(
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    """
    Get all security configuration values.
    Shows DB values, defaults, and source.
    ⚠️ ADMIN ONLY
    """
    configs = get_all_configs(db)
    
    # Count sources
    from_db = sum(1 for v in configs.values() if v["source"] == "database")
    from_default = sum(1 for v in configs.values() if v["source"] == "default")
    
    return {
        "total_configs": len(configs),
        "from_database": from_db,
        "from_defaults": from_default,
        "configs": configs,
    }


@router.post("/configs/refresh")
def refresh_configs(
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    """
    Force refresh configuration cache from database.
    ⚠️ ADMIN ONLY
    """
    count = refresh_config_cache(db)
    return {
        "status": "success",
        "configs_loaded": count,
        "message": f"Loaded {count} configurations from database",
    }