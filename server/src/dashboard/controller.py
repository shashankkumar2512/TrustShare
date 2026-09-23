from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.auth.dependencies import get_current_user
from src.dashboard import models, service
from src.database.core import get_db
from src.entities.user import User


router = APIRouter()


@router.get("/", response_model=models.DashboardResponse)
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.get_dashboard_data(db, current_user)
