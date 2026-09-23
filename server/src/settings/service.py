from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from src.auth.service import change_password as change_user_password
from src.entities.login_session import LoginSession
from src.entities.notification_channel_pref import NotificationChannelPreference
from src.entities.notification_pref import NotificationPreference
from src.entities.user import User
from src.settings.models import ACTIVITIES, NotificationPreferences, ProfileUpdate


DEFAULTS = {
    "file_shares": {"in_app": True, "email": True},
    "downloads": {"in_app": True, "email": False},
    "security_alerts": {"in_app": True, "email": True},
    "link_expirations": {"in_app": False, "email": True},
    "access_changes": {"in_app": True, "email": False},
    "system_updates": {"in_app": False, "email": False},
}


def update_profile(db: Session, user: User, data: ProfileUpdate) -> User:
    email = str(data.email).strip().lower()
    duplicate = (
        db.query(User)
        .filter(func.lower(User.email) == email, User.id != user.id)
        .first()
    )
    if duplicate:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email address is already in use.")
    user.name = data.name.strip()
    user.email = email
    user.organization = data.organization.strip() if data.organization else None
    user.avatar_url = data.avatar_url
    db.commit()
    db.refresh(user)
    return user


def change_password(db: Session, user: User, current_password: str, new_password: str) -> None:
    change_user_password(db, user, current_password, new_password)


def list_sessions(db: Session, user_id: int) -> list[LoginSession]:
    return (
        db.query(LoginSession)
        .filter(LoginSession.user_id == user_id)
        .order_by(LoginSession.is_current.desc(), LoginSession.created_at.desc())
        .all()
    )


def revoke_session(db: Session, user_id: int, session_id: int) -> None:
    session = (
        db.query(LoginSession)
        .filter(LoginSession.id == session_id, LoginSession.user_id == user_id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")
    if session.is_current:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The current session cannot be removed here.")
    db.delete(session)
    db.commit()


def revoke_other_sessions(db: Session, user_id: int) -> None:
    db.query(LoginSession).filter(
        LoginSession.user_id == user_id,
        LoginSession.is_current == False,
    ).delete(synchronize_session=False)
    db.commit()


def _digest_row(db: Session, user_id: int) -> NotificationPreference:
    row = db.query(NotificationPreference).filter(NotificationPreference.user_id == user_id).first()
    if not row:
        row = NotificationPreference(user_id=user_id, digest_frequency="daily")
        db.add(row)
        db.flush()
    return row


def _load_channel_prefs(db: Session, user_id: int) -> dict:
    """Internal helper: loads existing channel prefs and seeds missing ones without committing."""
    rows = {
        row.activity: row
        for row in db.query(NotificationChannelPreference).filter(
            NotificationChannelPreference.user_id == user_id
        )
    }
    for activity in ACTIVITIES:
        if activity not in rows:
            default = DEFAULTS[activity]
            row = NotificationChannelPreference(user_id=user_id, activity=activity, **default)
            db.add(row)
            rows[activity] = row
    return rows


def get_notification_preferences(db: Session, user_id: int) -> dict:
    digest = _digest_row(db, user_id)
    rows = _load_channel_prefs(db, user_id)
    db.commit()
    return {
        **{activity: {"in_app": rows[activity].in_app, "email": rows[activity].email} for activity in ACTIVITIES},
        "digest_frequency": digest.digest_frequency or "daily",
    }


def update_notification_preferences(db: Session, user_id: int, data: NotificationPreferences) -> dict:
    # FIX ISS-S5: single commit path — was previously committing twice (once here,
    # once inside get_notification_preferences). Consolidated into one atomic transaction.
    digest = _digest_row(db, user_id)
    digest.digest_frequency = data.digest_frequency
    rows = _load_channel_prefs(db, user_id)
    for activity in ACTIVITIES:
        values = getattr(data, activity)
        row = rows[activity]
        row.in_app = values.in_app
        row.email = values.email
    db.commit()
    return {
        **{activity: {"in_app": rows[activity].in_app, "email": rows[activity].email} for activity in ACTIVITIES},
        "digest_frequency": digest.digest_frequency or "daily",
    }