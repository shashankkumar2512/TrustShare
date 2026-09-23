"""
Automated tests for Settings Module — Milestone 2 Demo Integration Fixes.
Tests all 6 bug fixes + 2 feature additions.

Uses the SAME pattern as test_userAuth_service.py — direct PostgreSQL
via SessionLocal + TestClient, with explicit cleanup.

Usage:
    cd server
    python -m pytest tests/test_settings_service.py -v -s
"""
import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import text

from src.api import app
from src.database.core import SessionLocal
from src.entities.user import User
from src.entities.login_session import LoginSession
from src.auth.dependencies import hash_password, create_access_token
from src.auth import service as auth_service

client = TestClient(app)


# ═══════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def get_db_session() -> Session:
    return SessionLocal()


def _hard_cleanup(db: Session, user_id: int):
    """Delete all FK-referencing rows first, then user."""
    try:
        db.execute(text("DELETE FROM analytics_events WHERE user_id = :uid"), {"uid": user_id})
        db.execute(text("DELETE FROM login_sessions WHERE user_id = :uid"), {"uid": user_id})
        # Notification prefs tables may or may not exist depending on teammate's schema
        try:
            db.execute(text("DELETE FROM notification_channel_prefs WHERE user_id = :uid"), {"uid": user_id})
        except Exception:
            db.rollback()
        try:
            db.execute(text("DELETE FROM notification_prefs WHERE user_id = :uid"), {"uid": user_id})
        except Exception:
            db.rollback()
        db.commit()

        user = db.query(User).filter(User.id == user_id).first()
        if user:
            db.delete(user)
            db.commit()
    except Exception as e:
        print(f"[CLEANUP WARN] {e}", flush=True)
        db.rollback()


def create_test_user(email: str, mfa_enabled: bool = False, password: str = "Test@1234") -> User:
    db = get_db_session()
    try:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            _hard_cleanup(db, existing.id)

        user = User(
            name="Settings Test User",
            email=email,
            hashed_password=hash_password(password),
            role="member",
            plan="free",
            mfa_enabled=mfa_enabled,
            is_active=True,
            organization="TestCorp",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    finally:
        db.close()


def cleanup_user(email: str):
    db = get_db_session()
    try:
        user = db.query(User).filter(User.email == email).first()
        if user:
            _hard_cleanup(db, user.id)
    finally:
        db.close()


def get_auth_header(user_id: int) -> dict:
    token = create_access_token({"sub": str(user_id)})
    return {"Authorization": f"Bearer {token}"}


def get_user_from_db(user_id: int) -> User:
    db = get_db_session()
    try:
        return db.query(User).filter(User.id == user_id).first()
    finally:
        db.close()


def count_user_sessions(user_id: int) -> int:
    db = get_db_session()
    try:
        return db.query(LoginSession).filter(LoginSession.user_id == user_id).count()
    finally:
        db.close()


def create_login_session(user_id: int, is_current: bool = False) -> int:
    db = get_db_session()
    try:
        session = LoginSession(
            user_id=user_id,
            device_name="Test Device",
            browser_name="Chrome",
            device_type="desktop",
            ip_address="127.0.0.1",
            is_current=is_current,
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session.id
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture
def test_user():
    email = f"settings_{uuid.uuid4().hex[:8]}@demo.com"
    user = create_test_user(email)
    yield user
    cleanup_user(email)


@pytest.fixture
def test_user_mfa():
    email = f"settings_mfa_{uuid.uuid4().hex[:8]}@demo.com"
    user = create_test_user(email, mfa_enabled=True)
    yield user
    cleanup_user(email)


# ═══════════════════════════════════════════════════════════════════════════
# TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestSettingsDemoIntegrationFixes:
    """Verifies all Settings module demo integration fixes + feature additions."""

    # ── ISS-S5: Notification prefs single-commit path ──────────────────────
    def test_iss_s5_notification_prefs_update_persists(self, test_user):
        """Update returns correct values and persists in DB."""
        headers = get_auth_header(test_user.id)

        # Seed defaults via first GET
        r1 = client.get("/api/settings/notifications", headers=headers)
        assert r1.status_code == 200
        original = r1.json()
        assert original["digest_frequency"] == "daily"

        # Update
        payload = {
            **original,
            "file_shares": {"in_app": False, "email": False},
            "digest_frequency": "weekly",
        }
        r2 = client.put("/api/settings/notifications", headers=headers, json=payload)
        assert r2.status_code == 200
        updated = r2.json()
        assert updated["file_shares"]["in_app"] is False
        assert updated["digest_frequency"] == "weekly"

        # Verify persistence
        r3 = client.get("/api/settings/notifications", headers=headers)
        assert r3.json()["file_shares"]["in_app"] is False
        assert r3.json()["digest_frequency"] == "weekly"

    # ── Profile endpoints ──────────────────────────────────────────────────
    def test_profile_get_returns_user_data(self, test_user):
        headers = get_auth_header(test_user.id)
        r = client.get("/api/settings/profile", headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert data["email"] == test_user.email
        assert data["organization"] == "TestCorp"

    def test_profile_update_persists_organization(self, test_user):
        """ISS-S3 backend counterpart: organization field saves."""
        headers = get_auth_header(test_user.id)
        payload = {
            "name": "Updated Name",
            "email": test_user.email,
            "organization": "NewOrgCorp",
        }
        r = client.put("/api/settings/profile", headers=headers, json=payload)
        assert r.status_code == 200
        assert r.json()["organization"] == "NewOrgCorp"

        # Verify in DB
        fresh = get_user_from_db(test_user.id)
        assert fresh.organization == "NewOrgCorp"

    def test_profile_update_rejects_duplicate_email(self, test_user):
        """Duplicate email → 409."""
        other_email = f"other_{uuid.uuid4().hex[:8]}@demo.com"
        create_test_user(other_email)

        try:
            headers = get_auth_header(test_user.id)
            r = client.put("/api/settings/profile", headers=headers, json={
                "name": test_user.name,
                "email": other_email,
            })
            assert r.status_code == 409
            assert "already in use" in r.json()["detail"].lower()
        finally:
            cleanup_user(other_email)

    def test_profile_update_normalizes_email_to_lowercase(self, test_user):
        """Emails stored lowercase."""
        headers = get_auth_header(test_user.id)
        new_email = f"MIXED_{uuid.uuid4().hex[:8]}@EXAMPLE.COM"
        r = client.put("/api/settings/profile", headers=headers, json={
            "name": test_user.name,
            "email": new_email,
        })
        assert r.status_code == 200
        assert r.json()["email"] == new_email.lower()

        # Cleanup this renamed user (email changed from fixture-created one)
        try:
            cleanup_user(new_email.lower())
        except Exception:
            pass

    # ── Session isolation ──────────────────────────────────────────────────
    def test_sessions_list_returns_only_user_sessions(self, test_user):
        """User A cannot see User B's sessions."""
        create_login_session(test_user.id, is_current=True)
        create_login_session(test_user.id, is_current=False)

        other_email = f"other_{uuid.uuid4().hex[:8]}@demo.com"
        other = create_test_user(other_email)
        create_login_session(other.id, is_current=True)

        try:
            headers = get_auth_header(test_user.id)
            r = client.get("/api/settings/sessions", headers=headers)
            assert r.status_code == 200
            sessions = r.json()
            assert len(sessions) == 2
        finally:
            cleanup_user(other_email)

    def test_revoke_session_rejects_current(self, test_user):
        """Cannot revoke current session via endpoint."""
        current_id = create_login_session(test_user.id, is_current=True)
        headers = get_auth_header(test_user.id)

        r = client.delete(f"/api/settings/sessions/{current_id}", headers=headers)
        assert r.status_code == 400
        assert "current session" in r.json()["detail"].lower()

    def test_revoke_session_prevents_cross_user_deletion(self, test_user):
        """User B cannot delete User A's session by guessing ID."""
        target_id = create_login_session(test_user.id, is_current=False)

        other_email = f"other_{uuid.uuid4().hex[:8]}@demo.com"
        other = create_test_user(other_email)

        try:
            headers = get_auth_header(other.id)
            r = client.delete(f"/api/settings/sessions/{target_id}", headers=headers)
            assert r.status_code == 404

            # Original session still exists
            assert count_user_sessions(test_user.id) == 1
        finally:
            cleanup_user(other_email)

    def test_revoke_other_sessions_preserves_current(self, test_user):
        """Bulk revoke keeps current session alive."""
        create_login_session(test_user.id, is_current=True)
        create_login_session(test_user.id, is_current=False)
        create_login_session(test_user.id, is_current=False)
        assert count_user_sessions(test_user.id) == 3

        headers = get_auth_header(test_user.id)
        r = client.delete("/api/settings/sessions", headers=headers)
        assert r.status_code == 204

        # Only current session remains
        assert count_user_sessions(test_user.id) == 1

    # ── FEATURE: Password change invalidates other sessions ────────────────
    def test_password_change_invalidates_all_other_sessions(self, test_user):
        """Security fix: password change deletes all non-current sessions."""
        current_id = create_login_session(test_user.id, is_current=True)
        create_login_session(test_user.id, is_current=False)
        create_login_session(test_user.id, is_current=False)
        assert count_user_sessions(test_user.id) == 3

        headers = get_auth_header(test_user.id)
        r = client.post("/api/settings/change-password", headers=headers, json={
            "current_password": "Test@1234",
            "new_password": "NewPass@5678",
        })
        assert r.status_code == 200

        remaining = count_user_sessions(test_user.id)
        assert remaining == 1, f"Expected 1 (current only), got {remaining}"

    def test_password_change_wrong_current_preserves_sessions(self, test_user):
        """Failed password change must not affect sessions."""
        create_login_session(test_user.id, is_current=False)
        create_login_session(test_user.id, is_current=False)
        assert count_user_sessions(test_user.id) == 2

        headers = get_auth_header(test_user.id)
        r = client.post("/api/settings/change-password", headers=headers, json={
            "current_password": "WrongPassword",
            "new_password": "NewPass@5678",
        })
        assert r.status_code == 400

        # Sessions untouched
        assert count_user_sessions(test_user.id) == 2

    # ── FEATURE: MFA Setup Flow ────────────────────────────────────────────
    def test_mfa_setup_generates_and_stores_otp(self, test_user):
        """POST /mfa/setup → OTP stored, endpoint returns 200."""
        headers = get_auth_header(test_user.id)

        # Ensure clean OTP state
        auth_service.otp_store.pop(test_user.id, None)

        r = client.post("/api/auth/mfa/setup", headers=headers)
        assert r.status_code == 200
        assert r.json()["status"] == "otp_sent"

        # OTP should be in memory store
        assert test_user.id in auth_service.otp_store
        otp = auth_service.otp_store[test_user.id]["otp"]
        assert len(otp) == 6
        assert otp.isdigit()

    def test_mfa_setup_rejects_if_already_enabled(self, test_user_mfa):
        """Cannot setup if MFA already on."""
        headers = get_auth_header(test_user_mfa.id)
        r = client.post("/api/auth/mfa/setup", headers=headers)
        assert r.status_code == 400
        assert "already enabled" in r.json()["detail"].lower()

    def test_mfa_verify_setup_enables_mfa_on_correct_otp(self, test_user):
        """Correct OTP → mfa_enabled=True in DB."""
        headers = get_auth_header(test_user.id)

        # Setup first
        auth_service.otp_store.pop(test_user.id, None)
        client.post("/api/auth/mfa/setup", headers=headers)
        otp = auth_service.otp_store[test_user.id]["otp"]

        # Verify
        r = client.post("/api/auth/mfa/verify-setup", headers=headers, json={"code": otp})
        assert r.status_code == 200
        assert r.json()["mfa_enabled"] is True

        # Verify in DB
        fresh = get_user_from_db(test_user.id)
        assert fresh.mfa_enabled is True

    def test_mfa_verify_setup_rejects_wrong_code(self, test_user):
        """Wrong OTP → 400, MFA stays disabled."""
        headers = get_auth_header(test_user.id)

        auth_service.otp_store.pop(test_user.id, None)
        client.post("/api/auth/mfa/setup", headers=headers)

        r = client.post("/api/auth/mfa/verify-setup", headers=headers, json={"code": "000000"})
        assert r.status_code == 400

        fresh = get_user_from_db(test_user.id)
        assert fresh.mfa_enabled is False

    def test_mfa_disable_with_correct_password(self, test_user_mfa):
        """Password check passes → MFA disabled."""
        headers = get_auth_header(test_user_mfa.id)
        r = client.post(
            "/api/auth/mfa/disable-with-password",
            headers=headers,
            json={"password": "Test@1234"},
        )
        assert r.status_code == 200
        assert r.json()["mfa_enabled"] is False

        fresh = get_user_from_db(test_user_mfa.id)
        assert fresh.mfa_enabled is False

    def test_mfa_disable_with_wrong_password(self, test_user_mfa):
        """Wrong password → 400, MFA stays enabled."""
        headers = get_auth_header(test_user_mfa.id)
        r = client.post(
            "/api/auth/mfa/disable-with-password",
            headers=headers,
            json={"password": "WrongPassword"},
        )
        assert r.status_code == 400
        assert "incorrect" in r.json()["detail"].lower()

        fresh = get_user_from_db(test_user_mfa.id)
        assert fresh.mfa_enabled is True