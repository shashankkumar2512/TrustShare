from sqlalchemy.orm import Session
from src.entities.user import User
from src.users.models import UserUpdate
from fastapi import HTTPException

def get_all_users(db: Session):
    return db.query(User).all()

def get_user_by_id(db: Session, user_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail='User not found')
    return user

def update_user(db: Session, user: User, data: UserUpdate) -> User:
    if data.name is not None:
        user.name = data.name
    if data.email is not None:
        existing = db.query(User).filter(User.email == data.email, User.id != user.id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already taken")
        user.email = data.email
    if data.mfa_enabled is not None:
        user.mfa_enabled = data.mfa_enabled

    if data.organization is not None:
        user.organization = data.organization

    if data.avatar_url is not None:
        user.avatar_url = data.avatar_url
    db.commit()
    db.refresh(user)
    return user
