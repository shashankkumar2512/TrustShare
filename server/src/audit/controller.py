from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from src.database.core import get_db
from src.auth.dependencies import get_current_user, require_admin
from src.entities.user import User
from src.entities.audit_log import AuditLog
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()


class AuditLogOut(BaseModel):
    id: int
    user_id: Optional[int]
    action: str
    resource_type: Optional[str]
    resource_id: Optional[int]
    resource_name: Optional[str]
    ip_address: Optional[str]
    level: str
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/", response_model=list[AuditLogOut])
def list_audit_logs(
    limit: int = Query(50, le=200),
    skip: int = Query(0),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    return (
        db.query(AuditLog)
        .order_by(AuditLog.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
