import pytest
from fastapi import HTTPException

from src.entities.file import File
from src.entities.file_permission import FilePermission
from src.entities.notification import Notification
from src.entities.user import User
from src.shared_with_me.models import DirectShareCreate
from src.shared_with_me.service import (
    get_downloadable_shared_file,
    grant_direct_share,
    list_direct_shares,
    list_shared_files,
    revoke_direct_share,
)


def _user(db, name, email):
    user = User(name=name, email=email, hashed_password="not-used")
    db.add(user)
    db.flush()
    return user


def test_list_shared_files_returns_permission_and_owner_details(db):
    owner = _user(db, "Priya Sharma", "priya@example.com")
    recipient = _user(db, "Alex Morgan", "alex@example.com")
    file = File(original_name="Q3 Product Roadmap.pdf", stored_name="shared-roadmap.pdf", mimetype="application/pdf", size=2_400_000, encrypted=True, owner_id=owner.id)
    db.add(file)
    db.flush()
    db.add(FilePermission(file_id=file.id, user_id=recipient.id, granted_by=owner.id, permission_level="download"))
    db.commit()
    result = list_shared_files(db, recipient.id)
    assert result.total == 1
    assert result.downloadable == 1
    assert result.files[0].name == "Q3 Product Roadmap.pdf"
    assert result.files[0].shared_by == "Priya Sharma"
    assert result.files[0].can_download is True


def test_view_only_shared_file_cannot_be_downloaded(db):
    owner = _user(db, "Owner", "shared-owner@example.com")
    recipient = _user(db, "Recipient", "shared-recipient@example.com")
    file = File(original_name="read-only.txt", stored_name="shared-read-only.txt", mimetype="text/plain", size=20, encrypted=True, owner_id=owner.id)
    db.add(file)
    db.flush()
    db.add(FilePermission(file_id=file.id, user_id=recipient.id, granted_by=owner.id, permission_level="view"))
    db.commit()
    with pytest.raises(HTTPException) as exc:
        get_downloadable_shared_file(db, file.id, recipient.id)
    assert exc.value.status_code == 403


def test_owner_can_grant_update_list_and_revoke_direct_access(db):
    owner = _user(db, "Owner", "owner@example.com")
    recipient = _user(db, "Recipient", "recipient@example.com")
    file = File(
        original_name="team-plan.pdf",
        stored_name="team-plan.pdf",
        mimetype="application/pdf",
        size=100,
        encrypted=True,
        owner_id=owner.id,
    )
    db.add(file)
    db.commit()

    created = grant_direct_share(
        db,
        DirectShareCreate(file_id=file.id, recipient_email="RECIPIENT@example.com", permission="view"),
        owner.id,
    )
    assert created.permission == "view"
    assert list_shared_files(db, recipient.id).view_only == 1
    assert list_direct_shares(db, owner.id).total == 1
    assert db.query(Notification).filter(Notification.user_id == recipient.id).count() == 1

    updated = grant_direct_share(
        db,
        DirectShareCreate(file_id=file.id, recipient_email=recipient.email, permission="download"),
        owner.id,
    )
    assert updated.permission_id == created.permission_id
    assert updated.permission == "download"
    assert list_shared_files(db, recipient.id).downloadable == 1

    revoke_direct_share(db, created.permission_id, owner.id)
    assert list_shared_files(db, recipient.id).total == 0


def test_user_cannot_share_or_revoke_another_owners_file(db):
    owner = _user(db, "Owner", "owner-two@example.com")
    recipient = _user(db, "Recipient", "recipient-two@example.com")
    attacker = _user(db, "Attacker", "attacker@example.com")
    file = File(
        original_name="private.txt",
        stored_name="private.txt",
        mimetype="text/plain",
        size=10,
        encrypted=True,
        owner_id=owner.id,
    )
    db.add(file)
    db.commit()
    share = grant_direct_share(
        db,
        DirectShareCreate(file_id=file.id, recipient_email=recipient.email, permission="view"),
        owner.id,
    )

    with pytest.raises(HTTPException) as grant_error:
        grant_direct_share(
            db,
            DirectShareCreate(file_id=file.id, recipient_email=attacker.email, permission="view"),
            attacker.id,
        )
    assert grant_error.value.status_code == 404

    with pytest.raises(HTTPException) as revoke_error:
        revoke_direct_share(db, share.permission_id, attacker.id)
    assert revoke_error.value.status_code == 404
    assert list_shared_files(db, recipient.id).total == 1
