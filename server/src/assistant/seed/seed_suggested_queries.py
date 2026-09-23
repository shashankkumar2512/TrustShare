"""
Seed default suggested queries for the AI Assistant UI.
"""

import logging
from sqlalchemy.orm import Session

from src.entities.assistant_suggested_query import AssistantSuggestedQuery

logger = logging.getLogger(__name__)


DEFAULT_QUERIES = [
    # FILES CATEGORY
    {
        "query_text": "Show me my recent files",
        "category": "files",
        "icon_name": "FileText",
        "display_order": 1,
    },
    {
        "query_text": "Find all PDFs I uploaded this month",
        "category": "files",
        "icon_name": "FileSearch",
        "display_order": 2,
    },
    {
        "query_text": "What are my largest files?",
        "category": "files",
        "icon_name": "HardDrive",
        "display_order": 3,
    },
    # STORAGE CATEGORY
    {
        "query_text": "How much storage do I have left?",
        "category": "storage",
        "icon_name": "Database",
        "display_order": 4,
    },
    {
        "query_text": "Show my storage breakdown by category",
        "category": "storage",
        "icon_name": "PieChart",
        "display_order": 5,
    },
    # SHARES CATEGORY
    {
        "query_text": "What files have I shared with others?",
        "category": "shares",
        "icon_name": "Share2",
        "display_order": 6,
    },
    {
        "query_text": "Show my active share links",
        "category": "shares",
        "icon_name": "Link",
        "display_order": 7,
    },
    # ── ACCOUNT CATEGORY ────────────────────────────────
    {
        "query_text": "Show my active login sessions",
        "category": "account",
        "icon_name": "Monitor",
        "display_order": 8,
    },
    {
        "query_text": "Do I have any unread notifications?",
        "category": "account",
        "icon_name": "Bell",
        "display_order": 9,
    },
    {
        "query_text": "What's my account information?",
        "category": "account",
        "icon_name": "User",
        "display_order": 10,
    },
]


def seed_suggested_queries(db: Session) -> int:
    added = 0

    for q_data in DEFAULT_QUERIES:
        existing = (
            db.query(AssistantSuggestedQuery)
            .filter(AssistantSuggestedQuery.query_text == q_data["query_text"])
            .first()
        )

        if existing:
            continue

        query = AssistantSuggestedQuery(**q_data)
        db.add(query)
        added += 1

    if added > 0:
        db.commit()

    return added
