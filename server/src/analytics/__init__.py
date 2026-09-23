from fastapi import APIRouter
router = APIRouter()

# server/src/analytics/__init__.py
"""
TrustShare Analytics Module

Provides analytics + security dashboard functionality:
- Storage usage tracking
- Upload/download analytics
- Sharing analytics + top files + department breakdown
- Security events + login activity + unauthorized attempts
- Recent activity feed

All configuration values stored in `analytics_config` table — zero hardcoding.
"""