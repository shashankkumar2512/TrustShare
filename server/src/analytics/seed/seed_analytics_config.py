# server/src/analytics/seed/seed_analytics_config.py

import json
from sqlalchemy.orm import Session
from src.analytics.models.analytics_config import AnalyticsConfig
from src.analytics.constants import AnalyticsConfigKey


ANALYTICS_UI_CONFIG = {
    "tabs": [
        {"value": "analytics", "label": "File Analytics"},
        {"value": "security", "label": "Security"},
    ],

    "date_ranges": [
        {"value": "7days", "label": "Last 7 days"},
        {"value": "30days", "label": "Last 30 days"},
        {"value": "90days", "label": "Last 90 days"},
        {"value": "all", "label": "All Time"},
    ],

    "file_kpis": [
        {
            "key": "storage",
            "label": "Storage Used",
            "sub_key": "storage_subtitle",
            "icon": "HardDrive",
            "color_var": "--an-kpi-blue",
            "bg_var": "--an-kpi-blue-bg",
            "suffix": " GB",
            "decimals": 1,
        },
        {
            "key": "uploads",
            "label": "Files Uploaded",
            "sub_key": "uploads_subtitle",
            "icon": "Upload",
            "color_var": "--an-kpi-indigo",
            "bg_var": "--an-kpi-indigo-bg",
            "suffix": "",
            "decimals": 0,
        },
        {
            "key": "downloads",
            "label": "Downloads",
            "sub_key": "downloads_subtitle",
            "icon": "Download",
            "color_var": "--an-kpi-sky",
            "bg_var": "--an-kpi-sky-bg",
            "suffix": "",
            "decimals": 0,
        },
        {
            "key": "shares",
            "label": "Active Shares",
            "sub_key": "shares_subtitle",
            "icon": "Share2",
            "color_var": "--an-kpi-emerald",
            "bg_var": "--an-kpi-emerald-bg",
            "suffix": "",
            "decimals": 0,
        },
        {
            "key": "deletes",
            "label": "Files Deleted",
            "sub_key": "deletes_subtitle",
            "icon": "Trash2",
            "color_var": "--an-kpi-red",
            "bg_var": "--an-kpi-red-bg",
            "suffix": "",
            "decimals": 0,
        },
    ],

    "security_kpis": [
        {
            "key": "login_events",
            "label": "Successful Logins",
            "icon": "ShieldCheck",
            "color_var": "--an-kpi-emerald",
            "bg_var": "--an-kpi-emerald-bg",
            "suffix": "",
            "decimals": 0,
        },
        {
            "key": "failed_logins",
            "label": "Failed Attempts",
            "icon": "AlertCircle",
            "color_var": "--an-kpi-amber",
            "bg_var": "--an-kpi-amber-bg",
            "suffix": "",
            "decimals": 0,
        },
        {
            "key": "blocked_attacks",
            "label": "Blocked Attacks",
            "icon": "ShieldOff",
            "color_var": "--an-kpi-red",
            "bg_var": "--an-kpi-red-bg",
            "suffix": "",
            "decimals": 0,
        },
        {
            "key": "security_events",
            "label": "Security Events",
            "icon": "ShieldAlert",
            "color_var": "--an-kpi-blue",
            "bg_var": "--an-kpi-blue-bg",
            "suffix": "",
            "decimals": 0,
        },
    ],

    "charts": {
        "storage": {
            "title": "Storage Usage Over Time",
            "meta": "Last 7 months",
            "data_key": "gb",
            "x_key": "month",
            "value_label": "Storage (GB)",
            "empty": "No storage trend data yet.",
        },
        "volume": {
            "title": "Upload / Download Volume",
            "upload_label": "Uploads",
            "download_label": "Downloads",
            "empty": "No volume data yet.",
        },
        "login": {
            "title": "Login Activity — Last 7 Days",
            "success_label": "Success",
            "failed_label": "Failed",
            "empty": "No login activity data yet.",
        },
        "department": {
            "title": "Sharing by Department",
            "empty": "No sharing data yet.",
        },

        "file_types": {
            "title": "File Type Distribution",
            "subtitle": "Breakdown by file format",
            "meta": "by file count",
            "empty": "No files uploaded yet.",
            "total_label_singular": "File",
            "total_label_plural": "Files",
        },

        "login_heatmap": {
            "title": "Failed Login Heatmap",
            "subtitle": "Attack patterns by day and hour",
            "meta": "last 7 days",
            "empty": "No failed login attempts recorded.",
            "low_label": "Low",
            "high_label": "High",
        },
    },

    "panels": {
        "top_files": {
            "title": "Top Shared Files",
            "meta": "by opens",
            "opens_label": "opens",
            "downloads_label": "downloads",
            "empty": "No shared files yet.",
        },
        "timeline": {
            "title": "Security Event Timeline",
            "empty": "No security events.",
        },
        "unauthorized": {
            "title": "Unauthorized Access Attempts",
            "blocked_label": "blocked",
            "blocked_status": "Blocked",
            "flagged_status": "Flagged",
            "attempts_label": "attempts",
            "empty": "No unauthorized attempts recorded.",
        },
        "recent_activity": {
            "title": "Recent Activity",
            "meta": "audit log",
            "empty": "No recent activity.",
            "filter_all": "All users",
            "filter_placeholder": "Filter by user",
        },
        "system_stats": {
            "title": "System Health",
            "sections": {
                "activity": "Activity",
                "users":    "Users",
                "storage":  "Storage & Files",
                "performance": "Performance"
            },
            "labels": {
                "total_events":     "Total Events",
                "events_1h":        "Last Hour",
                "events_24h":       "Last 24h",
                "events_7d":        "Last 7 Days",
                "total_users":      "Total Users",
                "active_users_24h": "Active (24h)",
                "total_files":      "Active Files",
                "total_storage_mb": "Storage Used",
                "total_shares":     "Share Links",
                "active_shares":    "Active Shares",
                "db_response_ms":   "DB Response",
                "success_rate":     "Login Success",
                "python_version":   "Python",
                "platform":         "Platform"
            }
        },

        "top_active_users": {
            "title": "Top Active Users",
            "subtitle": "Most active workspace members",
            "meta": "by activity",
            "empty": "No user activity yet.",
            "events_label": "events",
            "event_singular": "event",
            "badge_prefix": "Top",
        },

        "security_score": {
            "title": "Security Score",
            "subtitle": "Overall security health",
            "meta": "0-100 scale",
            "empty": "Not enough data to calculate score.",
            "breakdown_title": "Score Breakdown",
            "login_success_label": "Login Success Rate",
            "attack_response_label": "Attack Response",
            "failed_score_label": "Failed Login Score",
        },

        "mfa_adoption": {
            "title": "MFA Adoption",
            "subtitle": "Multi-factor authentication usage",
            "meta": "across all users",
            "empty": "No user data available.",
            "enabled_label": "MFA Enabled",
            "disabled_label": "MFA Disabled",
            "recommendation_low": "Enable MFA for better security",
            "recommendation_good": "Great adoption rate!",
        },
    },

    "severity": {
        "blocked": {"label": "BLOCKED"},
        "flagged": {"label": "FLAGGED"},
        "warn": {"label": "WARN"},
        "info": {"label": "INFO"},
    },

    "page": {
        "title": "Analytics",
        "subtitle": "Workspace performance and security insights.",
        "export": {
            "idle": "Export Report",
            "exporting": "Exporting…",
            "exported": "Exported!",
        },
        "errors": {
            "load_failed": "Unable to load analytics.",
            "retry": "Try again",
        },
    },
}

DEFAULT_CONFIG = [
    {
        "key": AnalyticsConfigKey.STORAGE_TREND_MONTHS,
        "value": "7",
        "description": "Number of months shown in storage trend chart",
    },
    {
        "key": AnalyticsConfigKey.TOP_FILES_LIMIT,
        "value": "5",
        "description": "Number of top shared files shown",
    },
    {
        "key": AnalyticsConfigKey.LOGIN_CHART_DAYS,
        "value": "7",
        "description": "Number of days in login activity chart",
    },
    {
        "key": AnalyticsConfigKey.SECURITY_EVENTS_LIMIT,
        "value": "5",
        "description": "Number of events shown in security timeline",
    },
    {
        "key": AnalyticsConfigKey.UNAUTH_ATTEMPTS_LIMIT,
        "value": "10",
        "description": "Max unauthorized attempts shown in table",
    },
    {
        "key": AnalyticsConfigKey.VOLUME_WEEKS,
        "value": "5",
        "description": "Weeks shown in upload/download volume chart",
    },
    {
        "key": AnalyticsConfigKey.RECENT_ACTIVITY_LIMIT,
        "value": "10",
        "description": "Number of recent activity events shown",
    },
    {
        "key": AnalyticsConfigKey.HISTORY_DAYS,
        "value": "7",
        "description": "Days of daily upload/download history",
    },
    {
        "key": AnalyticsConfigKey.DEPT_SHARES_LIMIT,
        "value": "5",
        "description": "Number of departments shown in sharing donut",
    },
    {
        "key": AnalyticsConfigKey.DEPT_COLOR_PALETTE,
        "value": json.dumps([
            "#4F46E5",
            "#8B5CF6",
            "#06B6D4",
            "#10B981",
            "#F59E0B",
            "#EF4444",
            "#3B82F6",
            "#EC4899",
        ]),
        "description": "JSON array of hex colors for department donut",
    },
    {
        "key": AnalyticsConfigKey.DEFAULT_SEVERITY,
        "value": "info",
        "description": "Fallback severity level",
    },
    {
        "key": AnalyticsConfigKey.UI_CONFIG,
        "value": json.dumps(ANALYTICS_UI_CONFIG),
        "description": "Frontend analytics UI configuration as JSON",
    },
]


def seed_analytics_config(db: Session):
    for item in DEFAULT_CONFIG:
        row = (
            db.query(AnalyticsConfig)
            .filter(AnalyticsConfig.key == item["key"])
            .first()
        )

        if not row:
            db.add(AnalyticsConfig(**item))
        else:
            # Upsert: always update value + description
            row.value = item["value"]
            row.description = item.get("description")

    db.commit()