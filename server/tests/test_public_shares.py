from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException

from src.auth.dependencies import hash_password
from src.entities.file import File
from src.entities.share_link import ShareLink
from src.entities.user import User
from src.shares import service


def _public_share(db, *, token, password=None, expires_at=None, max_views=None, access_count=0, is_active=True):
    owner = User(name=f"Owner {token}", email=f"{token}@example.com", hashed_password="not-used")
    db.add(owner)
    db.flush()
    file = File(
        original_name=f"{token}.pdf",
        stored_name=f"{token}.pdf",
        mimetype="application/pdf",
        size=2048,
        encrypted=False,
        hash_sha256="not-used",
        owner_id=owner.id,
    )
    db.add(file)
    db.flush()
    share = ShareLink(
        file_id=file.id,
        token=token,
        permission="download",
        password_hash=hash_password(password) if password else None,
        expires_at=expires_at,
        max_views=max_views,
        access_count=access_count,
        is_active=is_active,
        created_by=owner.id,
    )
    db.add(share)
    db.commit()
    return owner, file, share


def test_share_link_uses_configured_frontend_url(monkeypatch):
    monkeypatch.setenv("FRONTEND_URL", "https://trustshare.example/")
    assert service._build_link("abc123") == "https://trustshare.example/s/abc123"


def test_public_details_return_safe_file_metadata_without_consuming_view(db):
    _, _, share = _public_share(db, token="public-details", max_views=3)

    result = service.inspect_public_share(db, share.token)

    assert result.file_name == "public-details.pdf"
    assert result.permission == "download"
    assert result.size == 2048
    assert result.password_required is False
    assert result.access_count == 0
    db.refresh(share)
    assert share.access_count == 0


def test_password_protected_public_details_require_valid_password(db):
    _, _, share = _public_share(db, token="protected-details", password="safe-pass")

    with pytest.raises(HTTPException) as missing:
        service.inspect_public_share(db, share.token)
    assert missing.value.status_code == 401

    with pytest.raises(HTTPException) as incorrect:
        service.inspect_public_share(db, share.token, "wrong-pass")
    assert incorrect.value.status_code == 401

    assert service.inspect_public_share(db, share.token, "safe-pass").password_required is True


@pytest.mark.parametrize(
    ("kwargs", "expected_status"),
    [
        ({"is_active": False}, 404),
        ({"expires_at": datetime.now(timezone.utc) - timedelta(minutes=1)}, 410),
        ({"max_views": 2, "access_count": 2}, 410),
    ],
)
def test_public_details_reject_unusable_links(db, kwargs, expected_status):
    token = f"unusable-{expected_status}-{len(kwargs)}"
    _, _, share = _public_share(db, token=token, **kwargs)

    with pytest.raises(HTTPException) as error:
        service.inspect_public_share(db, share.token)
    assert error.value.status_code == expected_status


def test_public_content_consumes_one_access_and_reuses_file_service(db, monkeypatch, tmp_path):
    _, file, share = _public_share(db, token="public-content", max_views=2)
    temporary_file = tmp_path / "download.pdf"
    temporary_file.write_bytes(b"document")
    monkeypatch.setattr(service, "log_event", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        "src.files.service.get_file_path",
        lambda db, file_id, owner_id, ip_address=None: (temporary_file, file.original_name),
    )

    path, name, mimetype, permission = service.get_public_file_path(db, share.token)

    assert path == temporary_file
    assert name == file.original_name
    assert mimetype == "application/pdf"
    assert permission == "download"
    db.refresh(share)
    assert share.access_count == 1
