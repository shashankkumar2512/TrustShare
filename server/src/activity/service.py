from sqlalchemy.orm import Session

from src.activity.models import ActivityCreate
from src.entities.audit_log import AuditLog


def create_activity(db: Session, activity_data: ActivityCreate):
    """Record an application activity in the project's shared audit trail."""
    new_activity = AuditLog(
        user_id=activity_data.user_id,
        action=activity_data.action,
        resource_type="file" if activity_data.file_name else "activity",
        resource_name=activity_data.file_name or activity_data.description,
        level="error" if "FAILED" in activity_data.action.upper() else "info",
    )

    db.add(new_activity)
    db.commit()
    db.refresh(new_activity)

    return new_activity


def get_user_activities(db: Session, user_id: int, limit: int = 100):
    return (
        db.query(AuditLog)
        .filter(AuditLog.user_id == user_id)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
        .all()
    )


def get_user_login_sessions(db: Session, user_id: int):
    """Retrieve all login sessions for the user from login_sessions table."""
    try:
        from src.entities.login_session import LoginSession
        sessions = (
            db.query(LoginSession)
            .filter(LoginSession.user_id == user_id)
            .order_by(LoginSession.is_current.desc(), LoginSession.id.desc())
            .all()
        )
        return sessions
    except Exception:
        return []