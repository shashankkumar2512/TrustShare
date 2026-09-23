# server/src/analytics/services/event_logger.py
"""
Reusable event logger — call this from any module (auth, files, shares, security)
to record an analytics event.

Example usage in auth module:
    from src.analytics.services import log_event
    from src.analytics.constants import AnalyticsEventType, AnalyticsEventStatus

    log_event(
        db,
        event_type=AnalyticsEventType.LOGIN,
        user_id=user.id,
        status=AnalyticsEventStatus.SUCCESS,
        ip_address=request.client.host,
    )
    db.commit()
"""

from sqlalchemy.orm import Session
from src.analytics.models.analytics_event import AnalyticsEvent
from src.analytics.constants import AnalyticsEventStatus


def log_event(
    db:               Session,
    event_type:       str,
    user_id:          int | None = None,
    file_id:          int | None = None,
    share_link_id:    int | None = None,
    status:           str        = AnalyticsEventStatus.SUCCESS,
    ip_address:       str | None = None,
    browser:          str | None = None,
    operating_system: str | None = None,
    device:           str | None = None,
    country:          str | None = None,
    city:             str | None = None,
    event_metadata:   dict | None = None,
) -> AnalyticsEvent:
    """
    Log an analytics event. Caller must commit the session.

    For security events, pass event_metadata with:
      - severity_key: str (must exist in analytics_severity_map)
      - label:  str  (e.g. "Brute force blocked")
      - detail: str  (e.g. "8 attempts from Kyiv, UA")
      - target: str  (e.g. "alex@acme.com")
      - attempts: int
    """
    event = AnalyticsEvent(
        event_type       = event_type,
        user_id          = user_id,
        file_id          = file_id,
        share_link_id    = share_link_id,
        status           = status,
        ip_address       = ip_address,
        browser          = browser,
        operating_system = operating_system,
        device           = device,
        country          = country,
        city             = city,
        event_metadata   = event_metadata,
    )
    db.add(event)
    return event