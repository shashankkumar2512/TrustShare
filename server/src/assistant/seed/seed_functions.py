"""
Seed default AI Assistant function definitions.

These schemas are what the LLM sees when deciding which function to call.
Python handlers with matching names must be registered in functions.py.
"""

import logging
from sqlalchemy.orm import Session

from src.entities.assistant_function import AssistantFunction

logger = logging.getLogger(__name__)


DEFAULT_FUNCTIONS = [
    # FILE OPERATIONS
    {
        "function_name": "list_files",
        "display_name": "List Files",
        "description": (
            "Get a list of the current user's files with optional filters. "
            "Use when user asks about their files, wants to see recent uploads, "
            "or wants to filter by type/date/size."
        ),
        "parameters_schema": {
            "type": "object",
            "properties": {
                "file_type": {
                    "type": "string",
                    "description": "Filter by category: 'pdf', 'image', 'video', 'document', 'archive', or 'all'",
                    "enum": ["pdf", "image", "video", "document", "archive", "all"],
                },
                "days_back": {
                    "type": "integer",
                    "description": "Only files uploaded in the last N days (e.g., 7 for last week, 30 for last month)",
                },
                "min_size_mb": {
                    "type": "number",
                    "description": "Minimum file size in megabytes",
                },
                "max_size_mb": {
                    "type": "number",
                    "description": "Maximum file size in megabytes",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max number of files to return (default 10, max 50)",
                },
            },
        },
        "category": "files",
        "requires_auth": True,
        "requires_admin": False,
        "display_order": 1,
    },
    {
        "function_name": "search_files",
        "display_name": "Search Files by Name",
        "description": (
            "Search for files by name using a keyword or phrase. "
            "Use when user is looking for a specific file by name or partial name."
        ),
        "parameters_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search keyword or phrase (e.g., 'invoice', 'Q4 report')",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max results to return (default 10, max 50)",
                },
            },
            "required": ["query"],
        },
        "category": "files",
        "requires_auth": True,
        "requires_admin": False,
        "display_order": 2,
    },
    # STORAGE INFO
    {
        "function_name": "get_storage_info",
        "display_name": "Get Storage Info",
        "description": (
            "Get the current user's storage usage: used, quota, and available space. "
            "Use when user asks about storage, space remaining, or capacity."
        ),
        "parameters_schema": {
            "type": "object",
            "properties": {},
        },
        "category": "storage",
        "requires_auth": True,
        "requires_admin": False,
        "display_order": 3,
    },
    {
        "function_name": "get_storage_breakdown",
        "display_name": "Get Storage Breakdown",
        "description": (
            "Get detailed breakdown of storage usage by file category "
            "(documents, media, archives, other). Use when user wants to see "
            "what's taking up space."
        ),
        "parameters_schema": {
            "type": "object",
            "properties": {},
        },
        "category": "storage",
        "requires_auth": True,
        "requires_admin": False,
        "display_order": 4,
    },
    #  SHARING
    {
        "function_name": "find_shares",
        "display_name": "Find Shares",
        "description": (
            "Get list of files the user has shared with others. Optionally "
            "filter by recipient email. Use when user asks who has access to "
            "their files or wants to review sharing activity."
        ),
        "parameters_schema": {
            "type": "object",
            "properties": {
                "recipient_email": {
                    "type": "string",
                    "description": "Filter shares by recipient email address",
                },
                "file_name": {
                    "type": "string",
                    "description": "Filter shares by file name (partial match)",
                },
                "active_only": {
                    "type": "boolean",
                    "description": "Only return non-expired, active shares (default true)",
                },
            },
        },
        "category": "shares",
        "requires_auth": True,
        "requires_admin": False,
        "display_order": 5,
    },
    # ACCOUNT
    {
        "function_name": "get_user_profile",
        "display_name": "Get User Profile",
        "description": (
            "Get the current user's profile: name, email, organization, plan, "
            "MFA status, member since date. Use when user asks about their "
            "account information."
        ),
        "parameters_schema": {
            "type": "object",
            "properties": {},
        },
        "category": "account",
        "requires_auth": True,
        "requires_admin": False,
        "display_order": 6,
    },
    {
        "function_name": "list_active_sessions",
        "display_name": "List Active Sessions",
        "description": (
            "Get list of the user's currently active login sessions with device "
            "info. Use when user asks about their logged-in devices or wants to "
            "review security."
        ),
        "parameters_schema": {
            "type": "object",
            "properties": {},
        },
        "category": "account",
        "requires_auth": True,
        "requires_admin": False,
        "display_order": 7,
    },
    {
        "function_name": "get_notifications",
        "display_name": "Get Notifications",
        "description": (
            "Get the user's recent notifications, optionally filtered to unread only. "
            "Use when user asks about notifications, alerts, or updates."
        ),
        "parameters_schema": {
            "type": "object",
            "properties": {
                "unread_only": {
                    "type": "boolean",
                    "description": "If true, only return unread notifications (default true)",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max notifications to return (default 10)",
                },
            },
        },
        "category": "account",
        "requires_auth": True,
        "requires_admin": False,
        "display_order": 8,
    },
]


def seed_functions(db: Session) -> int:
    """
    Insert missing function definitions. Returns count added.
    Existing functions are UPDATED to keep them in sync with code changes.
    """
    added = 0
    updated = 0

    for fn_data in DEFAULT_FUNCTIONS:
        existing = (
            db.query(AssistantFunction)
            .filter(AssistantFunction.function_name == fn_data["function_name"])
            .first()
        )

        if existing:
            changed = False
            if existing.description != fn_data["description"]:
                existing.description = fn_data["description"]
                changed = True
            if existing.parameters_schema != fn_data["parameters_schema"]:
                existing.parameters_schema = fn_data["parameters_schema"]
                changed = True
            if existing.display_name != fn_data["display_name"]:
                existing.display_name = fn_data["display_name"]
                changed = True
            if changed:
                updated += 1
            continue

        func = AssistantFunction(**fn_data)
        db.add(func)
        added += 1

    if added > 0 or updated > 0:
        db.commit()

    return added
