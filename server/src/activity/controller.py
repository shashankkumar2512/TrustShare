from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.activity.models import ActivityResponse, LoginSessionOut
from src.activity.service import get_user_activities, get_user_login_sessions
from src.auth.dependencies import get_current_user, require_admin
from src.database.core import get_db
from src.entities.user import User


router = APIRouter()


@router.get("/", response_model=list[ActivityResponse])
def list_activities(
    limit: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Members and admins: returns ONLY the authenticated user's own audit activity."""
    return get_user_activities(db, current_user.id, limit)


@router.get("/sessions", response_model=list[LoginSessionOut])
def list_login_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Members and admins: returns ONLY the authenticated user's own login sessions."""
    return get_user_login_sessions(db, current_user.id)


@router.get("/user/{user_id}", response_model=list[ActivityResponse])
def list_user_activities(
    user_id: int,
    limit: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """ADMIN ONLY: View any user's activity. Members cannot access this endpoint."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can view other users' activity.",
        )
    return get_user_activities(db, user_id, limit)


@router.get("/user/{user_id}/sessions", response_model=list[LoginSessionOut])
def list_user_sessions(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """ADMIN ONLY: View any user's login sessions. Members cannot access this endpoint."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can view other users' sessions.",
        )
    return get_user_login_sessions(db, user_id)