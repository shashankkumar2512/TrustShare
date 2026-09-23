# server/src/notifications/service.py

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.entities.notification import Notification
from src.entities.user import User
from src.entities.notification_channel_pref import NotificationChannelPreference

SECURITY_BYPASS_CATEGORIES = {"security"}

CATEGORY_TO_ACTIVITY = {
    "shares": "file_shares",
    "share": "file_shares",
    "downloads": "downloads",
    "download": "downloads",
    "security": "security_alerts",
    "expirations": "link_expirations",
    "expiration": "link_expirations",
    "access": "access_changes",
    "system": "system_updates",
}

# Match settings defaults
DEFAULTS = {
    "file_shares": {"in_app": True, "email": True},
    "downloads": {"in_app": True, "email": False},
    "security_alerts": {"in_app": True, "email": True},
    "link_expirations": {"in_app": False, "email": True},
    "access_changes": {"in_app": True, "email": False},
    "system_updates": {"in_app": False, "email": False},
}


def should_notify(
    db: Session,
    user_id: int,
    category: str,
    channel: str = "in_app"
) -> bool:
    """
    Check if user has disabled notifications for this category/channel in
    the NotificationChannelPreference database table.
    """
    if category in SECURITY_BYPASS_CATEGORIES:
        return True

    activity = CATEGORY_TO_ACTIVITY.get(category, category)

    pref = db.query(NotificationChannelPreference).filter(
        NotificationChannelPreference.user_id == user_id,
        NotificationChannelPreference.activity == activity
    ).first()

    if pref is not None:

        return bool(getattr(pref, channel, True))

    default_chan = DEFAULTS.get(activity, {})
    return bool(default_chan.get(channel, True))


def create_notification(
    db: Session,
    user_id: int,
    type: str,
    category: str,
    title: str,
    message: str,
    icon: str | None = None,
    resource_id: int | None = None,
    resource_type: str | None = None,
    commit: bool = False,
) -> Notification | None:
    
    if not should_notify(db, user_id, category, "in_app"):
        return None

    values = {
        "user_id": user_id,
        "type": type,
        "category": category,
        "title": title,
        "message": message,
    }
    if icon is not None:
        values["icon"] = icon
    if resource_id is not None:
        values["resource_id"] = resource_id
    if resource_type is not None:
        values["resource_type"] = resource_type

    notification = Notification(**values)
    db.add(notification)
    if commit:
        db.commit()
        db.refresh(notification)
    else:
        db.flush()
    return notification


def get_user_notifications(db: Session, user_id: int) -> list[Notification]:
    return (
        db.query(Notification)
        .filter(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc(), Notification.id.desc())
        .all()
    )


def mark_notification_read(db: Session, notification_id: int, user_id: int) -> Notification:
    notification = _user_notification(db, notification_id, user_id)
    if not notification.is_read:
        notification.is_read = True
        db.commit()
        db.refresh(notification)
    return notification


def mark_all_notifications_read(db: Session, user_id: int) -> int:
    updated = (
        db.query(Notification)
        .filter(Notification.user_id == user_id, Notification.is_read == False)
        .update({"is_read": True}, synchronize_session=False)
    )
    db.commit()
    return updated


def delete_notification(db: Session, notification_id: int, user_id: int) -> None:
    notification = _user_notification(db, notification_id, user_id)
    db.delete(notification)
    db.commit()


def delete_all_notifications(db: Session, user_id: int) -> int:
    deleted = (
        db.query(Notification)
        .filter(Notification.user_id == user_id)
        .delete(synchronize_session=False)
    )
    db.commit()
    return deleted


def _user_notification(db: Session, notification_id: int, user_id: int) -> Notification:
    notification = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.user_id == user_id)
        .first()
    )
    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")
    return notification