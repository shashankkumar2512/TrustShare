import re
import hashlib
from sqlalchemy.orm import Session

from src.entities.file import File
from src.entities.folder import Folder
from src.entities.share_link import ShareLink
from src.entities.notification import Notification
from src.entities.file_permission import FilePermission
from src.entities.file_content import FileContent
from src.security.secure_storage import load_encrypted_file
from src.security.encryption import decrypt_bytes
from src.security.key_manager import load_key
from src.file_summaries.text_extraction import extract_text

from src.entities.user import User


def _load_file_bytes(file: File) -> bytes:
    """Safely decrypt and load raw file bytes from storage."""
    try:
        encrypted = load_encrypted_file(file.stored_name)
        data = decrypt_bytes(encrypted, load_key(file.stored_name)) if file.encrypted else encrypted
        return data
    except Exception:
        return b""


def get_or_index_file_content(db: Session, file: File) -> str | None:
    """Retrieve existing indexed text for a file or extract and cache it in file_contents."""
    existing = db.query(FileContent).filter(FileContent.file_id == file.id).first()
    if existing:
        return existing.extracted_text

    try:
        raw_bytes = _load_file_bytes(file)
        if not raw_bytes:
            return None
        text = extract_text(file.original_name, raw_bytes)
        if not text:
            return None

        content_record = FileContent(
            file_id=file.id,
            extracted_text=text,
            char_count=len(text),
        )
        db.add(content_record)
        db.commit()
        db.refresh(content_record)
        return text
    except Exception:
        db.rollback()
        return None


def generate_match_snippet(text: str, query: str, context_window: int = 80) -> dict:
    """Find query in text with flexible whitespace and line break normalization."""
    q_clean = query.strip()
    if not q_clean or not text:
        return {"snippet": "", "match_count": 0}

    normalized_text = re.sub(r"\s+", " ", text).strip()
    words = [re.escape(w) for w in q_clean.split() if w]
    if not words:
        return {"snippet": normalized_text[:160] + ("..." if len(normalized_text) > 160 else ""), "match_count": 0}

    phrase_pattern = r"\s+".join(words)
    matches = list(re.finditer(phrase_pattern, normalized_text, re.IGNORECASE))

    if not matches and len(words) > 1:
        first_word_pattern = words[0]
        matches = list(re.finditer(first_word_pattern, normalized_text, re.IGNORECASE))

    if not matches:
        return {"snippet": normalized_text[:160] + ("..." if len(normalized_text) > 160 else ""), "match_count": 0}

    first_match = matches[0]
    start_idx = max(0, first_match.start() - context_window)
    end_idx = min(len(normalized_text), first_match.end() + context_window)

    prefix = "..." if start_idx > 0 else ""
    suffix = "..." if end_idx < len(normalized_text) else ""
    excerpt = normalized_text[start_idx:end_idx].strip()

    if list(re.finditer(phrase_pattern, excerpt, re.IGNORECASE)):
        highlighted_snippet = re.sub(
            f"({phrase_pattern})",
            r"<mark>\1</mark>",
            excerpt,
            flags=re.IGNORECASE
        )
    else:
        highlight_pattern = "|".join(words)
        highlighted_snippet = re.sub(
            f"({highlight_pattern})",
            r"<mark>\1</mark>",
            excerpt,
            flags=re.IGNORECASE
        )

    return {
        "snippet": f"{prefix}{highlighted_snippet}{suffix}",
        "raw_excerpt": excerpt,
        "match_count": len(matches),
    }


def content_search(db: Session, user_id: int, query: str, limit: int = 20) -> list[dict]:
    """Search inside file text contents for accessible files."""
    q = query.strip()
    if not q:
        return []

    owned_files = db.query(File).filter(
        File.owner_id == user_id,
        File.is_deleted == False,
    ).all()

    shared_files = (
        db.query(File)
        .join(FilePermission, FilePermission.file_id == File.id)
        .filter(
            FilePermission.user_id == user_id,
            File.is_deleted == False,
        )
        .all()
    )

    file_map = {f.id: f for f in owned_files + shared_files}

    results = []
    for file_id, file in file_map.items():
        text = get_or_index_file_content(db, file)
        if not text:
            continue

        snippet_info = generate_match_snippet(text, q)
        if snippet_info["match_count"] > 0:
            results.append({
                "id":            file.id,
                "original_name": file.original_name,
                "mimetype":      file.mimetype,
                "size":          file.size,
                "owner_id":      file.owner_id,
                "is_owner":      file.owner_id == user_id,
                "created_at":    file.created_at.isoformat() if file.created_at else None,
                "match_count":   snippet_info["match_count"],
                "snippet":       snippet_info["snippet"],
                "raw_excerpt":   snippet_info["raw_excerpt"],
                "score":         snippet_info["match_count"] * 10 + (100 if q.lower() in file.original_name.lower() else 0),
            })

    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:limit]


def search_shared_by_person(db: Session, user_id: int, query: str) -> list[dict]:
    
    q = query.strip()
    if not q:
        return []

    matching_sharers = (
        db.query(User)
        .filter(
            (User.name.ilike(f"%{q}%")) | (User.email.ilike(f"%{q}%")),
            User.id != user_id,
        )
        .limit(10)
        .all()
    )

    if not matching_sharers:
        return []

    sharer_ids = [u.id for u in matching_sharers]

    shared_files = (
        db.query(File, User)
        .join(FilePermission, FilePermission.file_id == File.id)
        .join(User, User.id == File.owner_id)
        .filter(
            FilePermission.user_id == user_id,
            File.owner_id.in_(sharer_ids),
            File.is_deleted == False,
        )
        .limit(5)
        .all()
    )

    return [
        {
            "id":            f.id,
            "original_name": f.original_name,
            "mimetype":      f.mimetype,
            "size":          f.size,
            "owner_id":      f.owner_id,
            "shared_by":     u.name or u.email,
            "shared_by_email": u.email,
        }
        for f, u in shared_files
    ]


def global_search(db: Session, user_id: int, query: str):
    q = query.strip()

    current_user = db.query(User).filter(User.id == user_id).first()
    is_admin = current_user and current_user.role == "admin"

    files = (
        db.query(File)
        .filter(
            File.owner_id == user_id,
            File.is_deleted == False,
            File.original_name.ilike(f"%{q}%"),
        )
        .limit(5)
        .all()
    )

    folders = (
        db.query(Folder)
        .filter(
            Folder.owner_id == user_id,
            Folder.name.ilike(f"%{q}%"),
        )
        .limit(5)
        .all()
    )

    shares = (
        db.query(ShareLink)
        .join(File, ShareLink.file_id == File.id)
        .filter(
            ShareLink.created_by == user_id,
            File.original_name.ilike(f"%{q}%"),
        )
        .limit(5)
        .all()
    )

    notifications = (
        db.query(Notification)
        .filter(
            Notification.user_id == user_id,
            Notification.title.ilike(f"%{q}%"),
        )
        .limit(5)
        .all()
    )

    content_matches = content_search(db, user_id, q, limit=5)

    if is_admin:
        users = (
            db.query(User)
            .filter(
                (User.name.ilike(f"%{q}%")) | (User.email.ilike(f"%{q}%"))
            )
            .limit(5)
            .all()
        )
        people_files = []
    else:
        users = []
        people_files = search_shared_by_person(db, user_id, q)

    return {
        "files": [
            {
                "id":            f.id,
                "original_name": f.original_name,
                "mimetype":      f.mimetype,
                "size":          f.size,
                "owner_id":      f.owner_id,
                "created_at":    f.created_at.isoformat() if f.created_at else None,
            }
            for f in files
        ],
        "folders": [
            {
                "id":       fo.id,
                "name":     fo.name,
                "owner_id": fo.owner_id,
            }
            for fo in folders
        ],
        "shares": [
            {
                "id":         s.id,
                "file_id":    s.file_id,
                "token":      s.token,
                "permission": s.permission,
                "is_active":  s.is_active,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in shares
        ],
        "notifications": [
            {
                "id":         n.id,
                "title":      n.title,
                "message":    n.message,
                "is_read":    n.is_read,
                "created_at": n.created_at.isoformat() if n.created_at else None,
            }
            for n in notifications
        ],
        "content_matches": content_matches,
        "users": [
            {
                "id":        u.id,
                "name":      u.name,
                "email":     u.email,
                "role":      u.role,
                "is_active": u.is_active,
            }
            for u in users
        ],
        "people_files": people_files,
    }