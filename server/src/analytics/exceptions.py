# server/src/analytics/exceptions.py

from src.exceptions import AppException


class AnalyticsServiceError(AppException):
    def __init__(self, detail: str = "Analytics service error"):
        super().__init__(status_code=500, detail=detail)


class AnalyticsConfigMissingError(AppException):
    def __init__(self, key: str):
        super().__init__(
            status_code=500,
            detail=f"Analytics config key missing: {key}",
        )