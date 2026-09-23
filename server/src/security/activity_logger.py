"""
Activity Logger Module — TrustShare Security

Dual-storage activity logging:
- PostgreSQL (primary — always available)
- MongoDB (secondary — per PSD requirement for activity logs)

Falls back to PostgreSQL-only if MongoDB unavailable.

References:
- PSD: Activity logs stored in MongoDB
- OWASP: Security Logging and Monitoring
"""

import os
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from src.security.config_loader import get_config

logger = logging.getLogger(__name__)

# MONGODB CONNECTION

_mongo_client = None
_mongo_db = None
_mongo_available = False

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "trustshare")
# THIS — was missing, causing NameError
MONGODB_COLLECTION = os.getenv("MONGODB_COLLECTION", "security_activity_logs")

def _get_collection_name(db=None):
    return get_config("MONGODB_COLLECTION", db, "security_activity_logs")

__all__ = [
    'log_security_activity',
    'get_recent_activities',
    'get_activity_stats',
    'is_mongodb_available',
    'initialize_mongodb',
]


def initialize_mongodb() -> bool:
    """
    Initialize MongoDB connection.
    
    Returns:
        True if MongoDB connected, False otherwise.
    """
    global _mongo_client, _mongo_db, _mongo_available
    
    try:
        from pymongo import MongoClient
        from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
        
        _mongo_client = MongoClient(
            MONGODB_URL,
            serverSelectionTimeoutMS=3000,
            connectTimeoutMS=3000,
        )
        
        # Test connection
        _mongo_client.admin.command('ping')
        
        _mongo_db = _mongo_client[MONGODB_DB_NAME]
        
        # Create indexes
        collection = _mongo_db[MONGODB_COLLECTION]
        collection.create_index("timestamp")
        collection.create_index("user_id")
        collection.create_index("action")
        collection.create_index("level")
        collection.create_index([("timestamp", -1)])
        
        _mongo_available = True
        logger.info(f"MongoDB connected: {MONGODB_URL}/{MONGODB_DB_NAME}")
        return True
        
    except ImportError:
        logger.info("pymongo not installed — MongoDB logging disabled")
        _mongo_available = False
        return False
        
    except Exception as e:
        logger.warning(f"MongoDB unavailable: {e} — Using PostgreSQL only")
        _mongo_available = False
        return False


# Try to connect on import
initialize_mongodb()


def is_mongodb_available() -> bool:
    """Check if MongoDB is available."""
    return _mongo_available


# LOGGING FUNCTIONS

def log_security_activity(
    action: str,
    user_id: Optional[int] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[int] = None,
    resource_name: Optional[str] = None,
    ip_address: Optional[str] = None,
    level: str = "info",
    metadata: Optional[Dict[str, Any]] = None,
    db=None,
) -> bool:
    """
    Log security activity to MongoDB (and PostgreSQL).
    
    Dual-write: Always writes to PostgreSQL audit_log.
    Additionally writes to MongoDB if available.
    
    Args:
        action: Activity action (UPLOAD, DOWNLOAD, LOGIN, etc.)
        user_id: User performing the action.
        resource_type: Type of resource (file, share_link, etc.)
        resource_id: Resource identifier.
        resource_name: Human-readable resource name.
        ip_address: Client IP address.
        level: Log level (info, warning, error, critical).
        metadata: Additional data to log.
        db: SQLAlchemy session for PostgreSQL logging.
        
    Returns:
        True if logged successfully.
    """
    now = datetime.now(timezone.utc)
    
    activity = {
        "action": action,
        "user_id": user_id,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "resource_name": resource_name,
        "ip_address": ip_address,
        "level": level,
        "metadata": metadata or {},
        "timestamp": now,
        "source": "security_module",
    }
    
    success = True
    
    # Write to PostgreSQL (always)
    if db:
        try:
            from src.entities.audit_log import AuditLog
            
            audit_log = AuditLog(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                resource_name=resource_name,
                level=level,
            )
            db.add(audit_log)
            # Don't commit here — let the caller handle transactions
        except Exception as e:
            logger.error(f"Failed to log to PostgreSQL: {e}")
            success = False
    
    # Write to MongoDB (if available)
    if _mongo_available and _mongo_db is not None:
        try:
            collection = _mongo_db[MONGODB_COLLECTION]
            
            # Convert datetime to ISO format for MongoDB
            mongo_doc = activity.copy()
            mongo_doc["timestamp"] = now.isoformat()
            
            collection.insert_one(mongo_doc)
            logger.debug(f"Logged to MongoDB: {action}")
            
        except Exception as e:
            logger.warning(f"Failed to log to MongoDB: {e}")
            # Don't fail — PostgreSQL is primary
    
    return success


# QUERY FUNCTIONS (MongoDB)

def get_recent_activities(
    limit: int = 50,
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    level: Optional[str] = None,
) -> list:
    """
    Get recent security activities from MongoDB.
    
    Falls back to empty list if MongoDB unavailable.
    """
    if not _mongo_available or _mongo_db is None:
        return []
    
    try:
        collection = _mongo_db[MONGODB_COLLECTION]
        
        query = {}
        if user_id:
            query["user_id"] = user_id
        if action:
            query["action"] = action
        if level:
            query["level"] = level
        
        cursor = (
            collection.find(query, {"_id": 0})
            .sort("timestamp", -1)
            .limit(limit)
        )
        
        return list(cursor)
        
    except Exception as e:
        logger.error(f"Failed to query MongoDB: {e}")
        return []


def get_activity_stats() -> dict:
    """Get activity statistics from MongoDB."""
    if not _mongo_available or _mongo_db is None:
        return {
            "mongodb_available": False,
            "message": "MongoDB not connected — using PostgreSQL only",
        }
    
    try:
        collection = _mongo_db[MONGODB_COLLECTION]
        
        total = collection.count_documents({})
        
        # Count by level
        stats = {
            "mongodb_available": True,
            "total_logs": total,
            "by_level": {},
        }
        
        for level in ["info", "warning", "error", "critical"]:
            count = collection.count_documents({"level": level})
            stats["by_level"][level] = count
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get MongoDB stats: {e}")
        return {"mongodb_available": False, "error": str(e)}