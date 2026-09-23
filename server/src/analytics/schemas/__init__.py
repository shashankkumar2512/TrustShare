# server/src/analytics/schemas/__init__.py

from .storage   import StorageResponse, StorageTrendPoint
from .uploads   import UploadAnalyticsResponse, UploadTrendItem, VolumeWeekPoint
from .downloads import DownloadAnalyticsResponse, DownloadTrendItem
from .deletes   import DeleteAnalyticsResponse
from .sharing   import SharingAnalyticsResponse, TopSharedFile, DepartmentShare
from .security  import (
    SecurityAnalyticsResponse,
    LoginActivityPoint,
    SecurityEventItem,
    UnauthorizedAttempt,
)
from .activity  import (
    RecentActivityResponse,
    RecentActivityItem,
    UserListResponse,
    UserListItem,
    SystemStatsResponse,
)
from .ui_config import AnalyticsUIConfigResponse
from .summary   import AnalyticsSummaryResponse