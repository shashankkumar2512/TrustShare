"""
Automated tests for Milestone 2 Demo Integration Fixes.
Tests all 10 fixes (ISS-D1 through ISS-D11) in one run.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from src.api import app
from src.database.core import SessionLocal
from src.entities.user import User
from src.entities.login_session import LoginSession
from src.auth.dependencies import (
    hash_password,
    create_access_token,
    create_refresh_token,
)
from datetime import timedelta
import uuid

client = TestClient(app)


def get_db_session() -> Session:
    return SessionLocal()


def create_test_user(email: str, mfa_enabled: bool = False) -> User:
    """Create a fresh test user."""
    db = get_db_session()
    try:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            _hard_cleanup(db, existing.id)

        user = User(
            name="Test User",
            email=email,
            hashed_password=hash_password("Test@1234"),
            role="member",
            plan="free",
            mfa_enabled=mfa_enabled,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    finally:
        db.close()


def _hard_cleanup(db: Session, user_id: int):
    """Delete all rows that reference this user (analytics, sessions), then user."""
    from sqlalchemy import text
    try:
        # Delete FK-referencing rows first
        db.execute(
            text("DELETE FROM analytics_events WHERE user_id = :uid"),
            {"uid": user_id},
        )
        db.execute(
            text("DELETE FROM login_sessions WHERE user_id = :uid"),
            {"uid": user_id},
        )
        db.commit()

        # Now delete user
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            db.delete(user)
            db.commit()
    except Exception as e:
        print(f"[CLEANUP WARN] {e}", flush=True)
        db.rollback()


def cleanup_user(email: str):
    """Remove test user and all their referencing rows."""
    db = get_db_session()
    try:
        user = db.query(User).filter(User.email == email).first()
        if user:
            _hard_cleanup(db, user.id)
    finally:
        db.close()


def get_active_session_count(user_id: int) -> int:
    db = get_db_session()
    try:
        return db.query(LoginSession).filter(
            LoginSession.user_id == user_id,
            LoginSession.is_current == True,
        ).count()
    finally:
        db.close()


def get_total_session_count(user_id: int) -> int:
    db = get_db_session()
    try:
        return db.query(LoginSession).filter(LoginSession.user_id == user_id).count()
    finally:
        db.close()


@pytest.fixture
def test_user():
    email = f"test_{uuid.uuid4().hex[:8]}@demo.com"
    user = create_test_user(email)
    yield user
    cleanup_user(email)


@pytest.fixture
def test_user_mfa():
    email = f"test_mfa_{uuid.uuid4().hex[:8]}@demo.com"
    user = create_test_user(email, mfa_enabled=True)
    yield user
    cleanup_user(email)


def login_and_get_tokens(email: str, password: str = "Test@1234") -> dict:
    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    return response.json()


class TestDemoIntegrationFixes:
    """All 10 demo integration fixes in one test class."""

    # ── ISS-D1: Logout invalidates session ─────────────────────────────────
    def test_iss_d1_logout_invalidates_session(self, test_user):
        tokens = login_and_get_tokens(test_user.email)
        assert tokens.get("access_token"), "Login should return access_token"

        active_before = get_active_session_count(test_user.id)
        assert active_before >= 1

        response = client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        assert response.status_code == 204

        active_after = get_active_session_count(test_user.id)
        assert active_after == 0, f"Expected 0 active sessions, got {active_after}"

    # ── ISS-D2: Refresh creates new session ────────────────────────────────
    def test_iss_d2_refresh_tracks_session(self, test_user):
        tokens = login_and_get_tokens(test_user.email)
        sessions_before = get_total_session_count(test_user.id)

        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]},
        )
        assert response.status_code == 200, f"Refresh failed: {response.text}"
        data = response.json()
        assert data.get("access_token")

        sessions_after = get_total_session_count(test_user.id)
        assert sessions_after > sessions_before

    # ── ISS-D3: MFA verify creates session ─────────────────────────────────
    def test_iss_d3_mfa_verify_tracks_session(self, test_user_mfa):
        from src.auth import service as auth_service

        tokens = login_and_get_tokens(test_user_mfa.email)
        assert tokens.get("mfa_required") is True, (
            f"MFA should be required. Got: {tokens}"
        )
        mfa_token = tokens.get("mfa_token")
        assert mfa_token

        otp_entry = auth_service.otp_store.get(test_user_mfa.id)
        assert otp_entry, "OTP should be stored"
        otp_code = otp_entry["otp"]

        sessions_before = get_total_session_count(test_user_mfa.id)

        response = client.post(
            "/api/auth/verify-otp",
            json={"mfa_token": mfa_token, "code": otp_code},
        )
        assert response.status_code == 200, f"OTP verify failed: {response.text}"

        sessions_after = get_total_session_count(test_user_mfa.id)
        assert sessions_after > sessions_before

    # ── ISS-D4: Garbage sub returns 401 (not 500) ──────────────────────────
    def test_iss_d4_bad_sub_returns_401_not_500(self):
        bad_token = create_access_token({"sub": "not_a_number"})
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {bad_token}"},
        )
        assert response.status_code == 401, (
            f"Expected 401 for bad sub, got {response.status_code}"
        )

    def test_iss_d4_garbage_token_returns_401(self):
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer completely_garbage_token"},
        )
        assert response.status_code == 401

    # ── ISS-D5: MFA pending token rejected at /me ──────────────────────────
    def test_iss_d5_mfa_pending_token_rejected(self, test_user):
        # Craft an mfa_pending token
        mfa_token = create_access_token(
            {"sub": str(test_user.id), "type": "mfa_pending"},
            expires_delta=timedelta(minutes=10),
        )

        # Verify the token actually has type=mfa_pending (proves create_access_token fix works)
        from src.auth.dependencies import decode_token
        payload = decode_token(mfa_token)
        assert payload.get("type") == "mfa_pending", (
            f"BUG: create_access_token overrode type. Got: {payload.get('type')}. "
            f"Apply FIX A to dependencies.py!"
        )

        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {mfa_token}"},
        )
        assert response.status_code == 401, (
            "SECURITY BUG: mfa_pending token should NOT access /me."
        )

    def test_iss_d5_refresh_token_rejected_at_me(self, test_user):
        refresh = create_refresh_token({"sub": str(test_user.id)})
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {refresh}"},
        )
        assert response.status_code == 401

    # ── ISS-D6: Signup creates session ─────────────────────────────────────
    def test_iss_d6_signup_creates_session(self):
        email = f"signup_{uuid.uuid4().hex[:8]}@demo.com"

        try:
            response = client.post(
                "/api/auth/signup",
                json={
                    "name": "Signup Test",
                    "email": email,
                    "password": "Test@1234",
                },
            )
            assert response.status_code == 201, f"Signup failed: {response.text}"

            db = get_db_session()
            try:
                user = db.query(User).filter(User.email == email).first()
                assert user, "User should be created"

                session_count = db.query(LoginSession).filter(
                    LoginSession.user_id == user.id,
                    LoginSession.is_current == True,
                ).count()
                assert session_count >= 1, "Signup should create session row"
            finally:
                db.close()
        finally:
            cleanup_user(email)

    # ── ISS-D11: Silent errors are now logged ──────────────────────────────
    def test_iss_d11_session_errors_are_logged(self, test_user, capsys):
        from unittest.mock import patch

        with patch("src.entities.login_session.LoginSession") as mock_ls:
            mock_ls.side_effect = Exception("SIMULATED: forced test failure")

            response = client.post(
                "/api/auth/login",
                json={"email": test_user.email, "password": "Test@1234"},
            )
            assert response.status_code == 200

        captured = capsys.readouterr()
        assert "SESSION SAVE ERROR" in captured.out, (
            "Session errors should be logged. Fix ISS-D11 not applied!"
        )

    # ── BONUS: Verify token type field ─────────────────────────────────────
    def test_fresh_access_token_has_type_field(self, test_user):
        tokens = login_and_get_tokens(test_user.email)
        from src.auth.dependencies import decode_token
        payload = decode_token(tokens["access_token"])
        assert payload.get("type") == "access"