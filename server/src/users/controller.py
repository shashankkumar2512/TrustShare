# server/src/users/controller.py

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from src.database.core import get_db
from src.users import models, service
from src.auth.dependencies import get_current_user, require_admin
from src.entities.user import User

router = APIRouter()

@router.get('/', response_model=list[models.UserOut])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)  
):
    return service.get_all_users(db)

@router.get('/search')
def search_teammates(
    q: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  
):
    users = (
        db.query(User)
        .filter(
            User.id != current_user.id,
            User.is_active == True,
            (User.name.ilike(f"%{q}%")) | (User.email.ilike(f"%{q}%"))
        )
        .limit(10)
        .all()
    )
    return [
        {
            "id": u.id,
            "name": u.name,
            "email_masked": u.email[:2] + "***" + u.email[u.email.index("@"):] if "@" in u.email else u.email
        }
        for u in users
    ]

@router.patch('/me', response_model=models.UserOut)
def update_current_user(
    data: models.UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.update_user(db, current_user, data)

@router.get('/{user_id}', response_model=models.UserOut)
def get_user(
    user_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  
):
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Forbidden: You cannot access other users' account-security metadata."
        )
    return service.get_user_by_id(db, user_id)