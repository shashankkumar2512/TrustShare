from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.database.core import get_db
from src.auth.dependencies import get_current_user
from src.entities.user import User

from .service import global_search, content_search

router = APIRouter()


@router.get("/")
def search(
    q: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return global_search(db, current_user.id, q)


@router.get("/content")
def search_content(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    results = content_search(db, current_user.id, q, limit=limit)
    return {
        "query": q,
        "total_results": len(results),
        "results": results,
    }