from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from src.auth.dependencies import get_current_user
from src.database.core import get_db
from src.entities.user import User
from src.settings import service
from src.settings.models import (
    MessageOut,
    NotificationPreferences,
    PasswordChange,
    ProfileOut,
    ProfileUpdate,
    SessionOut,
)


router = APIRouter()


@router.get("/profile", response_model=ProfileOut)
def profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/profile", response_model=ProfileOut)
def save_profile(
    data: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.update_profile(db, current_user, data)


@router.post("/change-password", response_model=MessageOut)
def save_password(
    data: PasswordChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service.change_password(db, current_user, data.current_password, data.new_password)
    return {"message": "Password changed successfully."}


@router.get("/sessions", response_model=list[SessionOut])
def sessions(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rows = service.list_sessions(db, current_user.id)
    return [
        SessionOut(
            id=row.id,
            device_name=row.device_name or "Unknown device",
            browser_name=row.browser_name or "Unknown browser",
            device_type=row.device_type or "unknown",
            ip_address=row.ip_address,
            location=row.location or "Unknown",
            last_active=row.last_active.isoformat() if row.last_active else None,
            is_current=bool(row.is_current),
        )
        for row in rows
    ]


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service.revoke_session(db, current_user.id, session_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/sessions", status_code=status.HTTP_204_NO_CONTENT)
def delete_other_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service.revoke_other_sessions(db, current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/notifications", response_model=NotificationPreferences)
def notification_preferences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.get_notification_preferences(db, current_user.id)


@router.put("/notifications", response_model=NotificationPreferences)
def save_notification_preferences(
    data: NotificationPreferences,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.update_notification_preferences(db, current_user.id, data)
