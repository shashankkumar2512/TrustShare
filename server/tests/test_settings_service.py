import pytest
from fastapi import HTTPException

from src.auth.dependencies import hash_password, verify_password
from src.entities.login_session import LoginSession
from src.entities.user import User
from src.settings.models import ChannelPreference, NotificationPreferences, ProfileUpdate
from src.settings.service import (
    change_password,
    get_notification_preferences,
    list_sessions,
    revoke_other_sessions,
    revoke_session,
    update_notification_preferences,
    update_profile,
)


def _user(db, name="Settings User", email="settings@example.com", password="Current@2026!"):
    user = User(name=name, email=email, hashed_password=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _preferences(**overrides):
    defaults = {
        "file_shares": ChannelPreference(in_app=True, email=True),
        "downloads": ChannelPreference(in_app=True, email=False),
        "security_alerts": ChannelPreference(in_app=True, email=True),
        "link_expirations": ChannelPreference(in_app=False, email=True),
        "access_changes": ChannelPreference(in_app=True, email=False),
        "system_updates": ChannelPreference(in_app=False, email=False),
        "digest_frequency": "daily",
    }
    defaults.update(overrides)
    return NotificationPreferences(**defaults)


def test_notification_preferences_are_created_and_persisted_per_channel(db):
    user = _user(db, email="notification-settings@example.com")
    initial = get_notification_preferences(db, user.id)
    assert initial["file_shares"] == {"in_app": True, "email": True}
    assert initial["digest_frequency"] == "daily"

    saved = update_notification_preferences(
        db,
        user.id,
        _preferences(
            file_shares=ChannelPreference(in_app=False, email=False),
            downloads=ChannelPreference(in_app=False, email=True),
            digest_frequency="weekly",
        ),
    )
    assert saved["file_shares"] == {"in_app": False, "email": False}
    assert saved["downloads"] == {"in_app": False, "email": True}
    assert saved["digest_frequency"] == "weekly"
    assert get_notification_preferences(db, user.id) == saved


def test_profile_and_password_updates_are_persisted_and_validated(db):
    user = _user(db, email="profile-settings@example.com")
    updated = update_profile(
        db,
        user,
        ProfileUpdate(
            name="Updated User",
            email="UPDATED@example.com",
            organization="Group D",
            avatar_url=None,
        ),
    )
    assert updated.name == "Updated User"
    assert updated.email == "updated@example.com"
    assert updated.organization == "Group D"

    change_password(db, user, "Current@2026!", "Changed@2026!")
    assert verify_password("Changed@2026!", user.hashed_password)
    with pytest.raises(HTTPException) as error:
        change_password(db, user, "wrong-password", "Another@2026!")
    assert error.value.status_code == 400


def test_session_listing_and_revocation_are_scoped_to_current_user(db):
    user = _user(db, email="session-settings@example.com")
    other = _user(db, name="Other", email="other-settings@example.com")
    current = LoginSession(user_id=user.id, device_name="Current", is_current=True)
    old = LoginSession(user_id=user.id, device_name="Old", is_current=False)
    foreign = LoginSession(user_id=other.id, device_name="Foreign", is_current=False)
    db.add_all([current, old, foreign])
    db.commit()

    assert [session.device_name for session in list_sessions(db, user.id)] == ["Current", "Old"]
    revoke_session(db, user.id, old.id)
    assert [session.device_name for session in list_sessions(db, user.id)] == ["Current"]

    with pytest.raises(HTTPException) as current_error:
        revoke_session(db, user.id, current.id)
    assert current_error.value.status_code == 400
    with pytest.raises(HTTPException) as foreign_error:
        revoke_session(db, user.id, foreign.id)
    assert foreign_error.value.status_code == 404

    extra = LoginSession(user_id=user.id, device_name="Extra", is_current=False)
    db.add(extra)
    db.commit()
    revoke_other_sessions(db, user.id)
    assert [session.device_name for session in list_sessions(db, user.id)] == ["Current"]
    assert db.query(LoginSession).filter(LoginSession.id == foreign.id).first() is not None
