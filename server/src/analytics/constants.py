# server/src/analytics/constants.py
"""
Analytics constants.

Important:
- These enums are code contracts.
- Config VALUES come from PostgreSQL tables.
"""

from enum import Enum


class AnalyticsEventType(str, Enum):
    LOGIN = "LOGIN"
    UPLOAD = "UPLOAD"
    DOWNLOAD = "DOWNLOAD"
    SHARE = "SHARE"
    DELETE = "DELETE"
    SECURITY = "SECURITY"


class AnalyticsEventStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    WARNING = "WARNING"


class SecuritySeverity(str, Enum):
    BLOCKED = "blocked"
    FLAGGED = "flagged"
    WARN = "warn"
    INFO = "info"


class AnalyticsConfigKey:
    STORAGE_TREND_MONTHS = "ANALYTICS_STORAGE_TREND_MONTHS"
    TOP_FILES_LIMIT = "ANALYTICS_TOP_FILES_LIMIT"
    LOGIN_CHART_DAYS = "ANALYTICS_LOGIN_CHART_DAYS"
    SECURITY_EVENTS_LIMIT = "ANALYTICS_SECURITY_EVENTS_LIMIT"
    UNAUTH_ATTEMPTS_LIMIT = "ANALYTICS_UNAUTH_ATTEMPTS_LIMIT"
    VOLUME_WEEKS = "ANALYTICS_VOLUME_WEEKS"
    RECENT_ACTIVITY_LIMIT = "ANALYTICS_RECENT_ACTIVITY_LIMIT"
    HISTORY_DAYS = "ANALYTICS_HISTORY_DAYS"
    DEPT_SHARES_LIMIT = "ANALYTICS_DEPT_SHARES_LIMIT"

    DEPT_COLOR_PALETTE = "ANALYTICS_DEPT_COLOR_PALETTE"
    DEFAULT_SEVERITY = "ANALYTICS_DEFAULT_SEVERITY"

    # Full frontend UI config stored as JSON in PostgreSQL
    UI_CONFIG = "ANALYTICS_UI_CONFIG"