# server/src/analytics/schemas/summary.py
"""
Analytics summary response schema.
FIX ISS-2: Added 6 missing fields that get_summary() returns
but were not in the schema. Schema is informational only since
/summary endpoint has no response_model — but kept accurate
for documentation and future use.
"""

from pydantic import BaseModel, ConfigDict
from typing import Any, Dict, List, Optional

from .storage   import StorageResponse
from .uploads   import UploadAnalyticsResponse
from .downloads import DownloadAnalyticsResponse
from .deletes   import DeleteAnalyticsResponse
from .sharing   import SharingAnalyticsResponse
from .security  import SecurityAnalyticsResponse
from .activity  import RecentActivityResponse, SystemStatsResponse


class AnalyticsSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    # Core sections (original)
    storage:         StorageResponse
    uploads:         UploadAnalyticsResponse
    downloads:       DownloadAnalyticsResponse
    deletes:         DeleteAnalyticsResponse
    sharing:         SharingAnalyticsResponse
    security:        SecurityAnalyticsResponse
    recent_activity: RecentActivityResponse
    system_stats:    SystemStatsResponse
    trends:          Dict[str, Any] = {}
    ui_config:       Dict[str, Any] = {}

    # FIX ISS-2: Missing fields now added
    # These are returned by get_summary() but were absent from schema
    file_types:            List[Dict[str, Any]] = []
    top_active_users:      List[Dict[str, Any]] = []
    security_score:        Dict[str, Any]       = {}
    failed_login_heatmap:  Dict[str, Any]       = {}
    mfa_adoption:          Dict[str, Any]       = {}
    performance_metrics:   Dict[str, Any]       = {}