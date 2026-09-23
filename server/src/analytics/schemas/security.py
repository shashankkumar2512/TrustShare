# server/src/analytics/schemas/security.py

from pydantic import BaseModel
from typing import List


class LoginActivityPoint(BaseModel):
    date:    str
    success: int
    failed:  int


class SecurityEventItem(BaseModel):
    id:     int
    label:  str
    detail: str
    time:   str
    sev:    str


class UnauthorizedAttempt(BaseModel):
    id:       int
    ip:       str
    location: str
    target:   str
    attempts: int
    time:     str
    blocked:  bool


class SecurityAnalyticsResponse(BaseModel):
    login_events:          int
    failed_logins:         int
    security_events:       int
    blocked_attacks:       int
    login_activity:        List[LoginActivityPoint]
    events:                List[SecurityEventItem]
    unauthorized_attempts: List[UnauthorizedAttempt]