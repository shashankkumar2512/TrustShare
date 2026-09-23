# server/src/analytics/schemas/ui_config.py
# Kept for backward compatibility — no longer used in summary response.
# ui_config is now passed as a plain Dict[str, Any] in summary.py.

from pydantic import BaseModel, ConfigDict
from typing import Any


class AnalyticsUIConfigResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    tabs:          Any = []
    date_ranges:   Any = []
    file_kpis:     Any = []
    security_kpis: Any = []
    charts:        Any = {}
    panels:        Any = {}
    severity:      Any = {}