from uuid import uuid4

from src.api import app
from src.auth.dependencies import get_current_user
from src.entities.file import File
from src.entities.folder import Folder
from src.entities.user import User


def _user(db, label):
    user = User(
        name=label,
        email=f"file-move-{label.lower()}-{uuid4().hex}@test.com",
        hashed_password="not-used",
    )
    db.add(user)
    db.flush()
    return user


def _file(db, owner, name="encrypted.pdf"):
    file = File(
        original_name=name,
        stored_name=f"{uuid4().hex}-{name}",
        mimetype="application/pdf",
        size=128,
        encrypted=True,
        hash_sha256="fixed-integrity-hash",
        owner_id=owner.id,
    )
    db.add(file)
    db.flush()
    return file


def _folder(db, owner, name="Destination"):
    folder = Folder(name=name, owner_id=owner.id)
    db.add(folder)
    db.flush()
    return folder


def _authenticate_as(user):
    app.dependency_overrides[get_current_user] = lambda: user


def test_move_endpoint_requires_authentication(client, db):
    owner = _user(db, "Unauthenticated")
    file = _file(db, owner)
    folder = _folder(db, owner)
    db.commit()

    response = client.patch(f"/api/files/{file.id}/move", json={"folder_id": folder.id})

    assert response.status_code == 401


def test_owner_can_move_encrypted_file_to_folder_and_back_to_root(client, db):
    owner = _user(db, "Owner")
    file = _file(db, owner)
    folder = _folder(db, owner)
    original_metadata = (file.stored_name, file.hash_sha256, file.encrypted)
    db.commit()
    _authenticate_as(owner)

    try:
        moved = client.patch(f"/api/files/{file.id}/move", json={"folder_id": folder.id})
        returned = client.patch(f"/api/files/{file.id}/move", json={"folder_id": None})
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert moved.status_code == 200
    assert moved.json()["folder_id"] == folder.id
    assert returned.status_code == 200
    assert returned.json()["folder_id"] is None
    db.refresh(file)
    assert (file.stored_name, file.hash_sha256, file.encrypted) == original_metadata


def test_move_rejects_another_users_file_or_target_folder(client, db):
    owner = _user(db, "First")
    other = _user(db, "Second")
    owners_file = _file(db, owner, "owners.pdf")
    others_file = _file(db, other, "others.pdf")
    owners_folder = _folder(db, owner, "Owners folder")
    others_folder = _folder(db, other, "Others folder")
    db.commit()
    _authenticate_as(owner)

    try:
        file_response = client.patch(
            f"/api/files/{others_file.id}/move", json={"folder_id": owners_folder.id}
        )
        folder_response = client.patch(
            f"/api/files/{owners_file.id}/move", json={"folder_id": others_folder.id}
        )
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert file_response.status_code == 404
    assert folder_response.status_code == 404
    db.refresh(owners_file)
    assert owners_file.folder_id is None
