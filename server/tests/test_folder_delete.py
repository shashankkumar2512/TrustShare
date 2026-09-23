from uuid import uuid4

import pytest
from fastapi import HTTPException

from src.entities.file import File
from src.entities.folder import Folder
from src.entities.user import User
from src.folders import service


def _user(db, label):
    user = User(
        name=label,
        email=f"folder-delete-{label.lower()}-{uuid4().hex}@test.com",
        hashed_password="not-used",
        storage_used=300,
    )
    db.add(user)
    db.flush()
    return user


def _folder(db, owner, name, parent_id=None):
    folder = Folder(name=name, owner_id=owner.id, parent_id=parent_id)
    db.add(folder)
    db.flush()
    return folder


def _file(db, owner, folder, name, size=100):
    file = File(
        original_name=name,
        stored_name=f"{uuid4().hex}-{name}",
        mimetype="application/pdf",
        size=size,
        encrypted=True,
        owner_id=owner.id,
        folder_id=folder.id,
    )
    db.add(file)
    db.flush()
    return file


def test_non_recursive_delete_keeps_non_empty_folder_safe(db):
    owner = _user(db, "Safe")
    folder = _folder(db, owner, "Evidence")
    _file(db, owner, folder, "report.pdf")
    db.commit()

    with pytest.raises(HTTPException) as error:
        service.delete_folder(db, folder.id, owner.id)

    assert error.value.status_code == 409
    assert db.query(Folder).filter_by(id=folder.id).one()


def test_recursive_delete_removes_nested_folders_and_soft_deletes_files(db, monkeypatch):
    owner = _user(db, "Recursive")
    root = _folder(db, owner, "Root")
    child = _folder(db, owner, "Child", root.id)
    grandchild = _folder(db, owner, "Grandchild", child.id)
    root_file = _file(db, owner, root, "root.pdf", 100)
    child_file = _file(db, owner, child, "child.pdf", 50)
    deleted_storage = []
    deleted_keys = []
    monkeypatch.setattr(service, "delete_encrypted_file", deleted_storage.append)
    monkeypatch.setattr(service, "delete_key", deleted_keys.append)
    db.commit()

    service.delete_folder(db, root.id, owner.id, recursive=True)

    assert db.query(Folder).filter(Folder.id.in_([root.id, child.id, grandchild.id])).count() == 0
    db.refresh(root_file)
    db.refresh(child_file)
    assert root_file.is_deleted is True and root_file.folder_id is None
    assert child_file.is_deleted is True and child_file.folder_id is None
    assert sorted(deleted_storage) == sorted([root_file.stored_name, child_file.stored_name])
    assert sorted(deleted_keys) == sorted([root_file.stored_name, child_file.stored_name])
    db.refresh(owner)
    assert owner.storage_used == 150


def test_recursive_delete_cannot_target_another_users_folder(db):
    owner = _user(db, "Owner")
    other = _user(db, "Other")
    folder = _folder(db, other, "Private")
    db.commit()

    with pytest.raises(HTTPException) as error:
        service.delete_folder(db, folder.id, owner.id, recursive=True)

    assert error.value.status_code == 404
    assert db.query(Folder).filter_by(id=folder.id).one()
