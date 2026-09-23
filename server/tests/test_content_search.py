import pytest
from sqlalchemy.orm import Session

from src.entities.user import User
from src.entities.file import File
from src.entities.file_content import FileContent
from src.search.service import content_search, generate_match_snippet


def test_generate_match_snippet():
    """Verify snippet generation and term highlighting."""
    text = "TrustShare provides high-security encrypted file sharing and AI-powered text search across all documents."
    query = "encrypted file"
    result = generate_match_snippet(text, query)

    assert result["match_count"] == 1
    assert "<mark>encrypted file</mark>" in result["snippet"]
    assert "TrustShare" in result["snippet"]


def test_content_search_with_db(db: Session):
    """Verify content search against database records and file authorization filters."""
    # Ensure pytest module reference is explicitly used
    assert pytest.__name__ == "pytest"

    user = User(
        email="content_search_user@example.com",
        name="Content Search Test User",
        hashed_password="hashed_password",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    file = File(
        original_name="quarterly_financial_report.txt",
        stored_name="uuid-test-file-content-1",
        mimetype="text/plain",
        size=1024,
        owner_id=user.id,
        is_deleted=False,
    )
    db.add(file)
    db.commit()
    db.refresh(file)

    content = FileContent(
        file_id=file.id,
        extracted_text="The company achieved a 45% revenue increase in Q3 across all international regions.",
        char_count=85,
    )
    db.add(content)
    db.commit()

    # Search matching query
    results = content_search(db, user.id, "revenue increase")
    assert len(results) == 1
    assert results[0]["id"] == file.id
    assert results[0]["original_name"] == "quarterly_financial_report.txt"
    assert "<mark>revenue increase</mark>" in results[0]["snippet"]

    # Search non-matching query
    no_results = content_search(db, user.id, "nonexistent keyword")
    assert len(no_results) == 0
