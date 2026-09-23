import hashlib
import os
from io import BytesIO
from uuid import uuid4

from fastapi import UploadFile

from src.auth.dependencies import hash_password
from src.entities.file import File
from src.entities.notification import Notification
from src.entities.user import User
from src.files import service as file_service
from src.folders.service import FolderCreate, create_folder
from src.shares import service as share_service


def _user(db, label, password="StrongPass1!"):
    user = User(
        name=label,
        email=f"notification-actions-{label.lower()}-{uuid4().hex}@test.com",
        hashed_password=hash_password(password),
    )
    db.add(user)
    db.commit()
    return user


def _titles(db, user_id):
    return [
        item.title
        for item in db.query(Notification)
        .filter(Notification.user_id == user_id)
        .order_by(Notification.id)
        .all()
    ]


def test_completed_login_creates_one_notification_but_mfa_pending_does_not(client, db, monkeypatch):
    normal = _user(db, "Normal")
    mfa_user = _user(db, "MFA")
    mfa_user.mfa_enabled = True
    db.commit()
    monkeypatch.setattr("src.auth.service.generate_otp", lambda *args, **kwargs: "123456")

    normal_response = client.post(
        "/api/auth/login",
        json={"email": normal.email, "password": "StrongPass1!"},
    )
    mfa_response = client.post(
        "/api/auth/login",
        json={"email": mfa_user.email, "password": "StrongPass1!"},
    )

    assert normal_response.status_code == 200
    assert _titles(db, normal.id).count("New login to your account") == 1
    assert mfa_response.status_code == 200
    assert mfa_response.json()["mfa_required"] is True
    assert _titles(db, mfa_user.id) == []


def test_upload_download_and_folder_create_generate_persisted_notifications(db, monkeypatch):
    user = _user(db, "Files")
    content = b"notification integration"
    monkeypatch.setattr(file_service, "validate_upload", lambda *args, **kwargs: None)
    monkeypatch.setattr(file_service, "generate_key", lambda: b"key")
    monkeypatch.setattr(file_service, "save_key", lambda *args: None)
    monkeypatch.setattr(file_service, "save_encrypted_file", lambda *args: None)
    monkeypatch.setattr(file_service, "encrypt_bytes", lambda data, key: data)
    monkeypatch.setattr(file_service, "load_key", lambda *args: b"key")
    monkeypatch.setattr(file_service, "load_encrypted_file", lambda *args: content)
    monkeypatch.setattr(file_service, "decrypt_bytes", lambda data, key: data)
    monkeypatch.setattr(file_service, "log_event", lambda *args, **kwargs: None)

    uploaded = file_service.upload_file(
        db,
        UploadFile(filename="evidence.txt", file=BytesIO(content)),
        user.id,
        None,
        True,
    )
    path, _ = file_service.get_file_path(db, uploaded.id, user.id)
    try:
        assert path.read_bytes() == content
    finally:
        os.remove(path)
    create_folder(db, FolderCreate(name="Evidence"), user.id)

    assert uploaded.hash_sha256 == hashlib.sha256(content).hexdigest()
    assert _titles(db, user.id)[-3:] == [
        "File uploaded",
        "File downloaded",
        "Folder created",
    ]


def test_public_share_creation_generates_owner_confirmation(db, monkeypatch):
    owner = _user(db, "Share")
    file = File(
        original_name="share-evidence.pdf",
        stored_name=f"share-{uuid4().hex}.pdf",
        mimetype="application/pdf",
        size=64,
        encrypted=True,
        owner_id=owner.id,
    )
    db.add(file)
    db.commit()
    monkeypatch.setattr(share_service, "log_event", lambda *args, **kwargs: None)

    share_service.create_share(
        db,
        share_service.ShareCreate(file_id=file.id, permission="view"),
        owner.id,
    )

    notification = db.query(Notification).filter_by(
        user_id=owner.id,
        title="Share link created",
    ).one()
    assert notification.category == "shares"
    assert "share-evidence.pdf" in notification.message
