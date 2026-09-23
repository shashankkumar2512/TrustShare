from datetime import datetime
from typing import Optional

class NotificationModel:
    """Data model representing internal notification entities."""
    def __init__(self, notification_id: str, title: str, body: str, created_at: Optional[datetime] = None):
        self.notification_id = notification_id
        self.title = title
        self.body = body
        self.created_at = created_at or datetime.utcnow()