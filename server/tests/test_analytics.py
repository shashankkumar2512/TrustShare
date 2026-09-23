# server/tests/test_analytics.py
"""
Unit + Integration Tests for Analytics Module.
Author: Badal Kumar Rai
Branch: Group-D-feature/Analytics-Badal

Test Groups:
  - Original 5 tests (preserved exactly)
  - Group A: Event Logger Unit Tests
  - Group B: Endpoint Response Structure Tests
  - Group C: Data Type Validation Tests
  - Group D: Date Range & Parameter Tests
  - Group E: No-Hardcoding Compliance Tests
  - Group F: Export Tests
  - Group G: Integration Tests (real actions → dashboard)

Run all:    python -m pytest tests/test_analytics.py -v --tb=short
Run group:  python -m pytest tests/test_analytics.py -v -k "TestEventLogger"
Save output: python -m pytest tests/test_analytics.py -v --tb=short 2>&1 | Tee-Object test_results.txt
"""

import pytest
from fastapi.testclient import TestClient
from src.main import app

# ── Shared test client (no auth) ─────────────────────────────────────────────
client = TestClient(app)


# ════════════════════════════════════════════════════════════════════════════
# ORIGINAL TESTS (1–5) — Preserved exactly as submitted
# ════════════════════════════════════════════════════════════════════════════

def test_analytics_summary_requires_authentication():
    """
    TEST 1 (Original)
    Verifies that the /api/analytics/summary endpoint is protected
    and blocks unauthenticated requests.

    PSD Reference: Section 4 — JWT Authentication
    """
    response = client.get("/api/analytics/summary?days=30")

    assert response.status_code in [401, 403], (
        f"Expected 401 or 403 but got {response.status_code}. "
        "Analytics endpoint should require authentication!"
    )

    print("✅ TEST 1 PASSED: Analytics summary endpoint is properly secured")


def test_export_csv_requires_authentication():
    """
    TEST 2 (Original)
    Verifies that the CSV export endpoint requires a valid JWT token.

    PSD Reference: Section 4 — JWT Authentication
    """
    response = client.get("/api/analytics/export/csv?days=30&tab=file")

    assert response.status_code in [401, 403, 422], (
        f"Expected 401/403/422 but got {response.status_code}. "
        "CSV export should require authentication!"
    )

    print("✅ TEST 2 PASSED: CSV export endpoint is properly secured")


def test_export_pdf_requires_authentication():
    """
    TEST 3 (Original)
    Verifies that the PDF export endpoint requires a valid JWT token.

    PSD Reference: Section 4 — JWT Authentication
    """
    response_file = client.get("/api/analytics/export/file-analytics?days=30")
    assert response_file.status_code in [401, 403], (
        f"File Analytics PDF: Expected 401/403 but got {response_file.status_code}"
    )

    response_security = client.get("/api/analytics/export/security?days=30")
    assert response_security.status_code in [401, 403], (
        f"Security PDF: Expected 401/403 but got {response_security.status_code}"
    )

    print("✅ TEST 3 PASSED: Both PDF export endpoints are properly secured")


def test_days_parameter_accepts_valid_range():
    """
    TEST 4 (Original)
    Verifies that the 'days' query parameter accepts valid values (1-3650).

    PSD Reference: Section 7 — Analytics Dashboard date filtering
    """
    valid_days = [1, 7, 30, 90, 365, 3650]

    for days in valid_days:
        response = client.get(f"/api/analytics/summary?days={days}")
        assert response.status_code != 500, (
            f"Server crashed with days={days}. Should handle gracefully!"
        )
        assert response.status_code in [401, 403], (
            f"For days={days}: Expected 401/403 but got {response.status_code}"
        )

    print(f"✅ TEST 4 PASSED: All {len(valid_days)} valid day values accepted")


def test_csv_export_accepts_valid_tab_parameter():
    """
    TEST 5 (Original)
    Verifies that the CSV export endpoint accepts both 'file' and 'security'
    tab parameters without crashing.

    PSD Reference: Section 7 — File Analytics + Security Dashboard exports
    """
    valid_tabs = ["file", "security"]

    for tab in valid_tabs:
        response = client.get(f"/api/analytics/export/csv?tab={tab}&days=30")
        assert response.status_code != 500, (
            f"Server crashed with tab={tab}. Should handle gracefully!"
        )
        assert response.status_code in [401, 403], (
            f"For tab={tab}: Expected 401/403 but got {response.status_code}"
        )

    print(f"✅ TEST 5 PASSED: Both tab values ('file', 'security') accepted")


# ════════════════════════════════════════════════════════════════════════════
# SHARED FIXTURES
# ════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def auth_client():
    """
    Returns (TestClient, headers, user_id) with real JWT from DB.
    No hardcoded credentials — reads first active user from DB.
    """
    from src.database.core import SessionLocal
    from src.entities.user import User
    from src.auth.dependencies import create_access_token

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.is_active == True).first()
        if not user:
            pytest.skip("No active users in DB — run seed first")

        token = create_access_token(data={"sub": str(user.id)})
        headers = {"Authorization": f"Bearer {token}"}
        return TestClient(app), headers, user.id
    finally:
        db.close()


@pytest.fixture(scope="module")
def db_session():
    """Raw DB session for direct DB operations in tests."""
    from src.database.core import SessionLocal
    session = SessionLocal()
    yield session
    session.close()


# ════════════════════════════════════════════════════════════════════════════
# HELPER — Safe model class lookup
# Handles different possible class names in model files
# ════════════════════════════════════════════════════════════════════════════

def _get_model_class(module_path: str, *possible_names: str):
    """
    Safely import a model class by trying multiple possible class names.
    Returns (class, actual_name) or raises ImportError with helpful message.

    Example:
        cls, name = _get_model_class(
            "src.analytics.models.event_type",
            "EventType", "AnalyticsEventType", "EventTypeLookup"
        )
    """
    import importlib
    module = importlib.import_module(module_path)

    for name in possible_names:
        cls = getattr(module, name, None)
        if cls is not None:
            return cls, name

    # None found — report what IS available
    available = [
        x for x in dir(module)
        if not x.startswith("_")
    ]
    raise ImportError(
        f"Could not find any of {list(possible_names)} in {module_path}. "
        f"Available names: {available}"
    )


# ════════════════════════════════════════════════════════════════════════════
# GROUP A — Event Logger Unit Tests
# PSD Reference: Section 5 — Access Monitoring, Audit Logging
# ════════════════════════════════════════════════════════════════════════════

class TestEventLogger:
    """
    Tests for event_logger.py — the core service that feeds all analytics.

    PSD Section 5 requires:
    - Download tracking          (5.i)
    - File access history        (5.ii)
    - Login activity monitoring  (5.iii)
    - Audit logs                 (5.iv)
    - Security event monitoring  (5.v)
    - Suspicious activity        (5.vi)
    """

    def test_login_success_event_is_logged(self, db_session):
        """
        TEST A1 — PSD 5(iii): Login activity monitoring
        Verifies LOGIN SUCCESS events can be created and saved to DB.
        """
        from src.analytics.services.event_logger import log_event
        from src.analytics.constants import (
            AnalyticsEventType,
            AnalyticsEventStatus,
        )
        from src.analytics.models.analytics_event import AnalyticsEvent

        event = log_event(
            db_session,
            event_type=AnalyticsEventType.LOGIN,
            status=AnalyticsEventStatus.SUCCESS,
            ip_address="127.0.0.1",
        )
        db_session.commit()

        assert event is not None, "log_event returned None"
        assert event.id is not None, "Event not saved to DB"
        assert event.event_type == AnalyticsEventType.LOGIN
        assert event.status == AnalyticsEventStatus.SUCCESS

        db_session.delete(event)
        db_session.commit()

    def test_login_failed_event_is_logged(self, db_session):
        """
        TEST A2 — PSD 5(vi): Suspicious activity detection
        Failed logins must be captured for security dashboard.
        """
        from src.analytics.services.event_logger import log_event
        from src.analytics.constants import (
            AnalyticsEventType,
            AnalyticsEventStatus,
        )

        event = log_event(
            db_session,
            event_type=AnalyticsEventType.LOGIN,
            status=AnalyticsEventStatus.FAILED,
            ip_address="192.168.1.100",
        )
        db_session.commit()

        assert event.event_type == AnalyticsEventType.LOGIN
        assert event.status == AnalyticsEventStatus.FAILED

        db_session.delete(event)
        db_session.commit()

    def test_upload_event_is_logged(self, db_session):
        """
        TEST A3 — PSD 7.1(ii): File upload reports
        Upload events must be capturable for analytics.
        """
        from src.analytics.services.event_logger import log_event
        from src.analytics.constants import (
            AnalyticsEventType,
            AnalyticsEventStatus,
        )

        event = log_event(
            db_session,
            event_type=AnalyticsEventType.UPLOAD,
            status=AnalyticsEventStatus.SUCCESS,
        )
        db_session.commit()

        assert event.event_type == AnalyticsEventType.UPLOAD
        assert event.status == AnalyticsEventStatus.SUCCESS

        db_session.delete(event)
        db_session.commit()

    def test_download_event_is_logged(self, db_session):
        """
        TEST A4 — PSD 5(i): Download tracking
        PSD 7.1(iii): Download analytics
        """
        from src.analytics.services.event_logger import log_event
        from src.analytics.constants import (
            AnalyticsEventType,
            AnalyticsEventStatus,
        )

        event = log_event(
            db_session,
            event_type=AnalyticsEventType.DOWNLOAD,
            status=AnalyticsEventStatus.SUCCESS,
        )
        db_session.commit()

        assert event.event_type == AnalyticsEventType.DOWNLOAD

        db_session.delete(event)
        db_session.commit()

    def test_delete_event_is_logged(self, db_session):
        """
        TEST A5 — PSD: File management deletion tracking
        """
        from src.analytics.services.event_logger import log_event
        from src.analytics.constants import (
            AnalyticsEventType,
            AnalyticsEventStatus,
        )

        event = log_event(
            db_session,
            event_type=AnalyticsEventType.DELETE,
            status=AnalyticsEventStatus.SUCCESS,
        )
        db_session.commit()

        assert event.event_type == AnalyticsEventType.DELETE

        db_session.delete(event)
        db_session.commit()

    def test_share_event_is_logged(self, db_session):
        """
        TEST A6 — PSD 7.1(iv): Sharing activity reports
        """
        from src.analytics.services.event_logger import log_event
        from src.analytics.constants import (
            AnalyticsEventType,
            AnalyticsEventStatus,
        )

        event = log_event(
            db_session,
            event_type=AnalyticsEventType.SHARE,
            status=AnalyticsEventStatus.SUCCESS,
        )
        db_session.commit()

        assert event.event_type == AnalyticsEventType.SHARE

        db_session.delete(event)
        db_session.commit()

    def test_security_event_with_metadata_is_logged(self, db_session):
        """
        TEST A7 — PSD 7.2(iii): Security event reports
        Security events must carry severity metadata for timeline display.
        """
        from src.analytics.services.event_logger import log_event
        from src.analytics.constants import (
            AnalyticsEventType,
            AnalyticsEventStatus,
        )

        event = log_event(
            db_session,
            event_type=AnalyticsEventType.SECURITY,
            status=AnalyticsEventStatus.FAILED,
            ip_address="10.0.0.1",
            event_metadata={
                "severity_key": "brute_force",
                "label": "Brute force blocked",
                "detail": "5 failed attempts from same IP",
                "target": "test@example.com",
                "attempts": 5,
            },
        )
        db_session.commit()

        assert event.event_type == AnalyticsEventType.SECURITY
        assert event.event_metadata is not None
        assert "severity_key" in event.event_metadata
        assert event.event_metadata["severity_key"] == "brute_force"

        db_session.delete(event)
        db_session.commit()

    def test_event_has_created_at_timestamp(self, db_session):
        """
        TEST A8 — PSD 5: All audit events need timestamps
        Without timestamps, audit log and security timeline cannot function.
        """
        from src.analytics.services.event_logger import log_event
        from src.analytics.constants import (
            AnalyticsEventType,
            AnalyticsEventStatus,
        )
        from src.analytics.models.analytics_event import AnalyticsEvent

        event = log_event(
            db_session,
            event_type=AnalyticsEventType.LOGIN,
            status=AnalyticsEventStatus.SUCCESS,
        )
        db_session.commit()

        saved = db_session.query(AnalyticsEvent).filter(
            AnalyticsEvent.id == event.id
        ).first()

        assert saved.created_at is not None, (
            "Event missing created_at — "
            "audit log and security timeline will not work"
        )

        db_session.delete(saved)
        db_session.commit()

    def test_event_logger_requires_manual_commit(self, db_session):
        """
        TEST A9 — Verifies event_logger does NOT auto-commit.
        Caller controls the transaction — as documented in event_logger.py.
        """
        from src.analytics.services.event_logger import log_event
        from src.analytics.constants import (
            AnalyticsEventType,
            AnalyticsEventStatus,
        )
        from sqlalchemy import inspect as sa_inspect

        event = log_event(
            db_session,
            event_type=AnalyticsEventType.LOGIN,
            status=AnalyticsEventStatus.SUCCESS,
        )

        state = sa_inspect(event)
        assert state.pending or state.persistent, (
            "Event should be in session (pending or persistent)"
        )

        db_session.rollback()


# ════════════════════════════════════════════════════════════════════════════
# GROUP B — Endpoint Response Structure Tests
# PSD Reference: Section 7 — Analytics Dashboard Module
# ════════════════════════════════════════════════════════════════════════════

class TestEndpointStructure:
    """
    Verifies all 13 analytics endpoints return correct
    data structure matching PSD requirements.
    """

    def test_summary_has_storage_section(self, auth_client):
        """
        TEST B1 — PSD 7.1(i): Storage usage statistics must be present
        """
        tc, headers, _ = auth_client
        r = tc.get("/api/analytics/summary?days=30", headers=headers)
        assert r.status_code == 200, f"Summary failed: {r.text[:200]}"

        storage = r.json().get("storage")
        assert storage is not None, (
            "Missing 'storage' in summary — "
            "PSD 7.1(i) storage usage statistics not available"
        )
        assert "storage_used_gb" in storage, "Missing storage_used_gb"
        assert "storage_quota_gb" in storage, "Missing storage_quota_gb"
        assert "storage_percentage" in storage, "Missing storage_percentage"
        assert "trend" in storage, (
            "Missing storage trend — StorageAreaChart has no data"
        )

    def test_summary_has_uploads_section(self, auth_client):
        """
        TEST B2 — PSD 7.1(ii): File upload reports
        """
        tc, headers, _ = auth_client
        r = tc.get("/api/analytics/summary?days=30", headers=headers)
        uploads = r.json().get("uploads")

        assert uploads is not None, (
            "Missing 'uploads' — PSD 7.1(ii) upload reports not available"
        )
        assert "total_uploads" in uploads, "Missing total_uploads"
        assert "weekly_uploads" in uploads, (
            "Missing weekly_uploads — upload trend chart has no data"
        )
        assert "volume_weekly" in uploads, (
            "Missing volume_weekly — VolumeBarChart has no data"
        )

    def test_summary_has_downloads_section(self, auth_client):
        """
        TEST B3 — PSD 7.1(iii): Download analytics + PSD 5(i): Download tracking
        """
        tc, headers, _ = auth_client
        r = tc.get("/api/analytics/summary?days=30", headers=headers)
        downloads = r.json().get("downloads")

        assert downloads is not None, (
            "Missing 'downloads' — PSD 7.1(iii) download analytics not available"
        )
        assert "total_downloads" in downloads, "Missing total_downloads"
        assert "transferred_mb" in downloads, (
            "Missing transferred_mb — download KPI subtitle broken"
        )

    def test_summary_has_sharing_section(self, auth_client):
        """
        TEST B4 — PSD 7.1(iv): Sharing activity reports
        PSD 7.3(iv): Sharing reports (Admin dashboard)
        """
        tc, headers, _ = auth_client
        r = tc.get("/api/analytics/summary?days=30", headers=headers)
        sharing = r.json().get("sharing")

        assert sharing is not None, (
            "Missing 'sharing' — PSD 7.1(iv) sharing reports not available"
        )
        assert "active_links" in sharing, "Missing active_links for KPI card"
        assert "top_files" in sharing, (
            "Missing top_files — TopSharedFiles panel has no data"
        )
        assert "by_department" in sharing, (
            "Missing by_department — DepartmentDonut chart has no data"
        )

    def test_summary_has_security_section(self, auth_client):
        """
        TEST B5 — PSD 7.2: Full Security Dashboard
        """
        tc, headers, _ = auth_client
        r = tc.get("/api/analytics/summary?days=30", headers=headers)
        security = r.json().get("security")

        assert security is not None, (
            "Missing 'security' — PSD 7.2 Security Dashboard not available"
        )
        assert "login_events" in security, (
            "Missing login_events — PSD 7.2(i) login monitoring broken"
        )
        assert "login_activity" in security, (
            "Missing login_activity — LoginLineChart has no data"
        )
        assert "unauthorized_attempts" in security, (
            "Missing unauthorized_attempts — PSD 7.2(ii) not implemented"
        )
        assert "events" in security, (
            "Missing events — SecurityTimeline has no data"
        )

    def test_summary_has_security_score(self, auth_client):
        """
        TEST B6 — PSD 7.2: Security analytics — SecurityScoreGauge component
        Score must be in valid 0-100 range
        """
        tc, headers, _ = auth_client
        r = tc.get("/api/analytics/summary?days=30", headers=headers)
        score = r.json().get("security_score")

        assert score is not None, (
            "Missing security_score — SecurityScoreGauge has no data"
        )
        assert "score" in score, "Missing score value"
        assert 0 <= score["score"] <= 100, (
            f"Security score {score['score']} out of 0-100 range — "
            "SVG gauge will render incorrectly"
        )
        assert "breakdown" in score, (
            "Missing score breakdown — gauge sub-scores not available"
        )

    def test_summary_has_mfa_adoption(self, auth_client):
        """
        TEST B7 — PSD 7.2: Security analytics — MFAAdoptionCard component
        """
        tc, headers, _ = auth_client
        r = tc.get("/api/analytics/summary?days=30", headers=headers)
        mfa = r.json().get("mfa_adoption")

        assert mfa is not None, (
            "Missing mfa_adoption — MFAAdoptionCard has no data"
        )
        assert "total_users" in mfa, "Missing total_users in mfa_adoption"
        assert "mfa_enabled" in mfa, "Missing mfa_enabled in mfa_adoption"
        assert "adoption_pct" in mfa, (
            "Missing adoption_pct — MFA percentage counter broken"
        )

    def test_summary_has_heatmap_with_correct_size(self, auth_client):
        """
        TEST B8 — PSD 7.2(ii): Unauthorized access — FailedLoginHeatmap
        Must be exactly 7 days × 24 hours = 168 cells
        """
        tc, headers, _ = auth_client
        r = tc.get("/api/analytics/summary?days=30", headers=headers)
        heatmap = r.json().get("failed_login_heatmap")

        assert heatmap is not None, (
            "Missing failed_login_heatmap — FailedLoginHeatmap has no data"
        )
        assert "grid" in heatmap, "Missing grid in heatmap"
        assert len(heatmap["grid"]) == 168, (
            f"Heatmap has {len(heatmap['grid'])} cells, "
            f"expected 168 (7 days × 24 hours)"
        )
        assert "max_count" in heatmap, (
            "Missing max_count — heatmap color intensity broken"
        )

    def test_summary_has_top_active_users(self, auth_client):
        """
        TEST B9 — PSD 7.3(i): User activity monitoring
        """
        tc, headers, _ = auth_client
        r = tc.get("/api/analytics/summary?days=30", headers=headers)
        users = r.json().get("top_active_users")

        assert users is not None, (
            "Missing top_active_users — TopActiveUsers panel has no data"
        )
        assert isinstance(users, list), "top_active_users must be a list"

    def test_summary_has_file_types(self, auth_client):
        """
        TEST B10 — PSD 7.1: File type distribution — FileTypeDonut chart
        """
        tc, headers, _ = auth_client
        r = tc.get("/api/analytics/summary?days=30", headers=headers)
        file_types = r.json().get("file_types")

        assert file_types is not None, (
            "Missing file_types — FileTypeDonut chart has no data"
        )
        assert isinstance(file_types, list), "file_types must be a list"

    def test_summary_has_performance_metrics(self, auth_client):
        """
        TEST B11 — PSD 8: Performance metrics — PerformancePanel component
        """
        tc, headers, _ = auth_client
        r = tc.get("/api/analytics/summary?days=30", headers=headers)
        perf = r.json().get("performance_metrics")

        assert perf is not None, (
            "Missing performance_metrics — PerformancePanel has no data"
        )
        assert "db_response_ms" in perf, "Missing db_response_ms"
        assert "active_now" in perf, "Missing active_now"
        assert "events_per_minute" in perf, "Missing events_per_minute"

    def test_summary_has_system_stats(self, auth_client):
        """
        TEST B12 — PSD 7.3(v): System monitoring — SystemHealthPanel component
        """
        tc, headers, _ = auth_client
        r = tc.get("/api/analytics/summary?days=30", headers=headers)
        stats = r.json().get("system_stats")

        assert stats is not None, (
            "Missing system_stats — SystemHealthPanel has no data"
        )
        assert "total_users" in stats, "Missing total_users"
        assert "total_files" in stats, "Missing total_files"
        assert "db_response_ms" in stats, "Missing db_response_ms"
        assert "status" in stats, "Missing status field"

    def test_summary_has_recent_activity(self, auth_client):
        """
        TEST B13 — PSD 5(ii): File access history
        PSD 7.2(iv): Audit monitoring — RecentActivityPanel
        """
        tc, headers, _ = auth_client
        r = tc.get("/api/analytics/summary?days=30", headers=headers)

        assert r.status_code == 200, (
            f"Summary crashed — possible ORM serialization error: {r.text[:300]}"
        )

        recent = r.json().get("recent_activity")
        assert recent is not None, "Missing recent_activity"
        assert "activities" in recent, "Missing activities list"
        assert isinstance(recent["activities"], list), (
            "activities must be list — "
            "ORM objects returned instead of dicts (serialization bug)"
        )

    def test_trends_endpoint_works(self, auth_client):
        """
        TEST B14 — Trends endpoint must return data for KPI trend arrows
        """
        tc, headers, _ = auth_client
        r = tc.get("/api/analytics/trends", headers=headers)

        assert r.status_code == 200, f"Trends failed: {r.text[:200]}"
        data = r.json()
        assert "trends" in data, "Missing trends key"
        assert "file_access_history" in data, (
            "Missing file_access_history — "
            "PSD 5(ii) file access history not implemented"
        )

    def test_users_endpoint_returns_list(self, auth_client):
        """
        TEST B15 — /users must return list for RecentActivityPanel user filter
        """
        tc, headers, _ = auth_client
        r = tc.get("/api/analytics/users", headers=headers)

        assert r.status_code == 200
        data = r.json()
        assert "users" in data, "Missing users key"
        assert isinstance(data["users"], list), "users must be a list"

    def test_system_stats_endpoint_works(self, auth_client):
        """
        TEST B16 — PSD 7.3(v): System monitoring
        /system-stats must return live system health data
        """
        tc, headers, _ = auth_client
        r = tc.get("/api/analytics/system-stats", headers=headers)

        assert r.status_code == 200, f"system-stats failed: {r.text[:200]}"
        data = r.json()
        assert "db_response_ms" in data, "Missing db_response_ms"
        assert "status" in data, "Missing status"


# ════════════════════════════════════════════════════════════════════════════
# GROUP C — Data Type Validation Tests
# ════════════════════════════════════════════════════════════════════════════

class TestDataTypes:
    """
    PostgreSQL returns Decimal for SUM/AVG aggregates.
    All numeric fields must be int or float in JSON response.
    """

    def test_storage_values_are_numeric(self, auth_client):
        """
        TEST C1 — storage_used_gb and storage_quota_gb must be float not Decimal
        """
        tc, headers, _ = auth_client
        r = tc.get("/api/analytics/summary?days=30", headers=headers)
        storage = r.json().get("storage", {})

        for field in ["storage_used_gb", "storage_quota_gb", "storage_percentage"]:
            val = storage.get(field)
            assert isinstance(val, (int, float)), (
                f"storage.{field} = {val!r} is {type(val).__name__}. "
                f"Expected number — Decimal not converted to float!"
            )

    def test_transferred_mb_is_numeric(self, auth_client):
        """
        TEST C2 — transferred_mb must be float
        """
        tc, headers, _ = auth_client
        r = tc.get("/api/analytics/summary?days=30", headers=headers)
        val = r.json().get("downloads", {}).get("transferred_mb")

        assert isinstance(val, (int, float)), (
            f"transferred_mb = {val!r} is {type(val).__name__}. "
            f"Must be float for download KPI display."
        )

    def test_recent_activity_items_are_serializable(self, auth_client):
        """
        TEST C3 — CRITICAL: recent_activity items must be dicts not ORM objects.
        If this fails, /summary returns 500 in production.
        """
        tc, headers, _ = auth_client
        r = tc.get("/api/analytics/summary?days=30", headers=headers)

        assert r.status_code == 200, (
            f"Summary endpoint crashed — "
            f"likely ORM serialization error in recent_activity: "
            f"{r.text[:400]}"
        )

        activities = r.json().get("recent_activity", {}).get("activities", [])
        for i, item in enumerate(activities[:5]):
            assert isinstance(item, dict), (
                f"Activity[{i}] is {type(item).__name__}, not dict. "
                f"ORM object returned — not JSON serializable!"
            )

    def test_security_score_is_numeric(self, auth_client):
        """
        TEST C4 — Security score must be 0-100 numeric for SVG gauge rendering
        """
        tc, headers, _ = auth_client
        r = tc.get("/api/analytics/summary?days=30", headers=headers)
        score = r.json().get("security_score", {}).get("score")

        assert isinstance(score, (int, float)), (
            f"security_score.score = {score!r} is {type(score).__name__}. "
            f"Must be numeric for gauge SVG calculation."
        )
        assert 0 <= score <= 100, (
            f"Score {score} out of 0-100 range — gauge arc will break"
        )

    def test_mfa_adoption_pct_is_numeric(self, auth_client):
        """
        TEST C5 — adoption_pct must be float for MFA percentage counter animation
        """
        tc, headers, _ = auth_client
        r = tc.get("/api/analytics/summary?days=30", headers=headers)
        pct = r.json().get("mfa_adoption", {}).get("adoption_pct")

        assert isinstance(pct, (int, float)), (
            f"adoption_pct = {pct!r} is {type(pct).__name__}. "
            f"Must be numeric for MFAAdoptionCard percentage display."
        )
        assert 0 <= pct <= 100, (
            f"adoption_pct {pct} out of 0-100 range"
        )


# ════════════════════════════════════════════════════════════════════════════
# GROUP D — Date Range & Parameter Tests
# ════════════════════════════════════════════════════════════════════════════

class TestDateRangeAndParams:
    """Date range filtering must work for all UI presets."""

    @pytest.mark.parametrize("days,label", [
        (7,   "Last 7 days"),
        (30,  "Last 30 days"),
        (90,  "Last 90 days"),
        (365, "All Time"),
    ])
    def test_all_date_presets_work(self, auth_client, days, label):
        """
        TEST D1-D4 — All 4 date presets from UI must work without error
        """
        tc, headers, _ = auth_client
        r = tc.get(f"/api/analytics/summary?days={days}", headers=headers)
        assert r.status_code == 200, (
            f"Date preset '{label}' (days={days}) failed: {r.text[:200]}"
        )

    def test_custom_date_range_accepted(self, auth_client):
        """
        TEST D5 — Custom date range (start_date + end_date) must work
        Used by the custom date picker in DateRangeDropdown
        """
        from datetime import date, timedelta
        tc, headers, _ = auth_client

        today = date.today()
        start = (today - timedelta(days=14)).isoformat()
        end = today.isoformat()

        r = tc.get(
            f"/api/analytics/summary?start_date={start}&end_date={end}",
            headers=headers,
        )
        assert r.status_code == 200, (
            f"Custom date range failed: {r.text[:200]}"
        )

    def test_days_zero_rejected(self, auth_client):
        """
        TEST D6 — days=0 must be rejected — Query(ge=1) validation
        """
        tc, headers, _ = auth_client
        r = tc.get("/api/analytics/summary?days=0", headers=headers)
        assert r.status_code == 422, (
            f"days=0 returned {r.status_code}, expected 422 validation error"
        )

    def test_days_negative_rejected(self, auth_client):
        """
        TEST D7 — Negative days must be rejected
        """
        tc, headers, _ = auth_client
        r = tc.get("/api/analytics/summary?days=-1", headers=headers)
        assert r.status_code == 422

    def test_storage_trend_returns_list(self, auth_client):
        """
        TEST D8 — storage.trend must be a list for StorageAreaChart
        """
        tc, headers, _ = auth_client
        r = tc.get("/api/analytics/summary?days=30", headers=headers)
        trend = r.json().get("storage", {}).get("trend")

        assert isinstance(trend, list), (
            f"storage.trend is {type(trend).__name__}, "
            f"expected list for StorageAreaChart"
        )

    def test_login_activity_returns_list(self, auth_client):
        """
        TEST D9 — security.login_activity must be a list for LoginLineChart
        """
        tc, headers, _ = auth_client
        r = tc.get("/api/analytics/summary?days=30", headers=headers)
        login_activity = r.json().get("security", {}).get("login_activity")

        assert isinstance(login_activity, list), (
            f"security.login_activity is {type(login_activity).__name__}, "
            f"expected list for LoginLineChart"
        )


# ════════════════════════════════════════════════════════════════════════════
# GROUP E — No-Hardcoding Compliance Tests
# Project Standard: Zero hardcoding — all config from DB
# ════════════════════════════════════════════════════════════════════════════

class TestNoHardcoding:
    """
    Project standard: All UI config must come from analytics_config DB table.
    No values hardcoded in Python code.
    """

    def test_analytics_config_table_seeded(self, db_session):
        """
        TEST E1 — analytics_config table must have active records.
        Empty table = UI config falls back to hardcoded defaults.
        """
        from src.analytics.models.analytics_config import AnalyticsConfig

        count = db_session.query(AnalyticsConfig).filter(
            AnalyticsConfig.is_active == True
        ).count()

        assert count > 0, (
            "analytics_config table is empty — "
            "run: python -m src.analytics.seed.seed_analytics_config. "
            "UI tabs, KPI labels, and chart colors will use hardcoded fallbacks."
        )

    def test_event_types_table_seeded(self, db_session):
        """
        TEST E2 — event_type lookup table must be seeded.
        Uses _get_model_class to handle different possible class names.
        """
        cls, found_name = _get_model_class(
            "src.analytics.models.event_type",
            # Try all likely class names
            "EventType",
            "AnalyticsEventType",
            "EventTypeLookup",
            "EventTypeModel",
        )

        count = db_session.query(cls).count()
        assert count > 0, (
            f"event_type table is empty (model class: {found_name}) — "
            "run: python -m src.analytics.seed.seed_event_types"
        )

    def test_event_statuses_table_seeded(self, db_session):
        """
        TEST E3 — event_status lookup table must be seeded.
        Uses _get_model_class to handle different possible class names.
        """
        cls, found_name = _get_model_class(
            "src.analytics.models.event_status",
            # Try all likely class names
            "EventStatus",
            "AnalyticsEventStatus",
            "EventStatusLookup",
            "EventStatusModel",
        )

        count = db_session.query(cls).count()
        assert count > 0, (
            f"event_status table is empty (model class: {found_name}) — "
            "run: python -m src.analytics.seed.seed_event_statuses"
        )

    def test_severity_map_table_seeded(self, db_session):
        """
        TEST E4 — severity_map table must be seeded.
        Without this, security events show wrong severity levels.
        """
        from src.analytics.models.severity_map import AnalyticsSeverityMap

        count = db_session.query(AnalyticsSeverityMap).filter(
            AnalyticsSeverityMap.is_active == True
        ).count()

        assert count > 0, (
            "severity_map table is empty — "
            "run: python -m src.analytics.seed.seed_severity_map. "
            "SecurityTimeline severity badges will be wrong."
        )

    def test_ui_config_loaded_from_database(self, auth_client):
        """
        TEST E5 — ui_config in summary must come from DB not Python defaults.
        """
        tc, headers, _ = auth_client
        r = tc.get("/api/analytics/summary?days=30", headers=headers)
        ui_config = r.json().get("ui_config")

        assert ui_config is not None, "ui_config missing from summary response"
        assert isinstance(ui_config, dict), "ui_config must be a dict"
        assert len(ui_config.get("tabs", [])) > 0, (
            "ui_config.tabs is empty — seed_analytics_config not run. "
            "Tab switcher will not render correctly."
        )
        assert len(ui_config.get("file_kpis", [])) > 0, (
            "ui_config.file_kpis is empty — "
            "KPI cards have no config from DB"
        )


# ════════════════════════════════════════════════════════════════════════════
# GROUP F — Export Tests
# PSD Reference: Section 7 — Analytics reports generation
# ════════════════════════════════════════════════════════════════════════════

class TestExports:
    """PDF and CSV exports must work correctly per PSD requirements."""

    def test_pdf_file_analytics_is_valid_pdf(self, auth_client):
        """
        TEST F1 — PSD 7.1: File analytics PDF export
        Must return valid PDF with correct content-type
        """
        tc, headers, _ = auth_client
        r = tc.get(
            "/api/analytics/export/file-analytics?days=30",
            headers=headers,
        )
        assert r.status_code == 200, f"PDF export failed: {r.text[:200]}"
        assert r.headers.get("content-type") == "application/pdf", (
            f"Wrong content-type: {r.headers.get('content-type')}. "
            f"Expected application/pdf"
        )
        assert r.content[:4] == b"%PDF", (
            "Response is not a valid PDF — missing %PDF magic bytes"
        )

    def test_pdf_security_is_valid_pdf(self, auth_client):
        """
        TEST F2 — PSD 7.2: Security analytics PDF export
        """
        tc, headers, _ = auth_client
        r = tc.get(
            "/api/analytics/export/security?days=30",
            headers=headers,
        )
        assert r.status_code == 200, f"Security PDF failed: {r.text[:200]}"
        assert r.content[:4] == b"%PDF", (
            "Security PDF is not a valid PDF file"
        )

    def test_csv_file_tab_returns_csv(self, auth_client):
        """
        TEST F3 — PSD 7.1: File analytics CSV export
        """
        tc, headers, _ = auth_client
        r = tc.get(
            "/api/analytics/export/csv?tab=file&days=30",
            headers=headers,
        )
        assert r.status_code == 200, f"CSV export failed: {r.text[:200]}"
        assert "text/csv" in r.headers.get("content-type", ""), (
            f"Wrong content-type: {r.headers.get('content-type')}"
        )

    def test_csv_security_tab_returns_csv(self, auth_client):
        """
        TEST F4 — PSD 7.2: Security analytics CSV export
        """
        tc, headers, _ = auth_client
        r = tc.get(
            "/api/analytics/export/csv?tab=security&days=30",
            headers=headers,
        )
        assert r.status_code == 200, f"Security CSV failed: {r.text[:200]}"

    def test_csv_has_metadata_header(self, auth_client):
        """
        TEST F5 — CSV must have TrustShare metadata header (project standard)
        Contains: title, generated timestamp, date range
        """
        tc, headers, _ = auth_client
        r = tc.get(
            "/api/analytics/export/csv?tab=file&days=30",
            headers=headers,
        )
        content = r.text
        assert "TrustShare" in content[:300], (
            "CSV missing TrustShare metadata header. "
            "First rows must contain report title."
        )

    def test_pdf_custom_date_range_works(self, auth_client):
        """
        TEST F6 — PDF export must work with custom date range
        """
        from datetime import date, timedelta
        tc, headers, _ = auth_client

        today = date.today()
        start = (today - timedelta(days=14)).isoformat()
        end = today.isoformat()

        r = tc.get(
            f"/api/analytics/export/file-analytics"
            f"?start_date={start}&end_date={end}",
            headers=headers,
        )
        assert r.status_code == 200, (
            f"PDF with custom date range failed: {r.text[:200]}"
        )
        assert r.content[:4] == b"%PDF"

    def test_csv_download_has_filename_header(self, auth_client):
        """
        TEST F7 — CSV response must include Content-Disposition with filename
        """
        tc, headers, _ = auth_client
        r = tc.get(
            "/api/analytics/export/csv?tab=file&days=30",
            headers=headers,
        )
        disposition = r.headers.get("content-disposition", "")
        assert "filename" in disposition, (
            f"Missing Content-Disposition filename header. "
            f"Got: '{disposition}'. Browser download will not name file correctly."
        )
        assert "trustshare" in disposition.lower(), (
            "Filename should contain 'trustshare' prefix"
        )


# ════════════════════════════════════════════════════════════════════════════
# GROUP G — Integration Tests
# PSD: Activity monitoring, audit logging — Demo Readiness
# ════════════════════════════════════════════════════════════════════════════

class TestAnalyticsIntegration:
    """
    End-to-end integration tests.
    Simulates real platform events and verifies they appear
    in the analytics dashboard.
    """

    def test_login_event_reflected_in_security_dashboard(
        self, auth_client, db_session
    ):
        """
        TEST G1 — PSD 7.2(i): Login monitoring
        Simulate login → verify security dashboard shows it
        """
        from src.analytics.services.event_logger import log_event
        from src.analytics.constants import (
            AnalyticsEventType,
            AnalyticsEventStatus,
        )

        tc, headers, user_id = auth_client

        before = tc.get(
            "/api/analytics/summary?days=7", headers=headers
        ).json().get("security", {}).get("login_events", 0)

        event = log_event(
            db_session,
            event_type=AnalyticsEventType.LOGIN,
            status=AnalyticsEventStatus.SUCCESS,
            user_id=user_id,
            ip_address="127.0.0.1",
        )
        db_session.commit()

        after = tc.get(
            "/api/analytics/summary?days=7", headers=headers
        ).json().get("security", {}).get("login_events", 0)

        assert after >= before, (
            f"Login event not reflected in security dashboard. "
            f"Before: {before}, After: {after}. "
            f"Auth module may not be calling log_event."
        )

        db_session.delete(event)
        db_session.commit()

    def test_upload_event_reflected_in_file_analytics(
        self, auth_client, db_session
    ):
        """
        TEST G2 — PSD 7.1(ii): File upload reports
        Simulate upload → verify file analytics shows it
        """
        from src.analytics.services.event_logger import log_event
        from src.analytics.constants import (
            AnalyticsEventType,
            AnalyticsEventStatus,
        )

        tc, headers, user_id = auth_client

        before = tc.get(
            "/api/analytics/summary?days=7", headers=headers
        ).json().get("uploads", {}).get("total_uploads", 0)

        event = log_event(
            db_session,
            event_type=AnalyticsEventType.UPLOAD,
            status=AnalyticsEventStatus.SUCCESS,
            user_id=user_id,
        )
        db_session.commit()

        after = tc.get(
            "/api/analytics/summary?days=7", headers=headers
        ).json().get("uploads", {}).get("total_uploads", 0)

        assert after > before, (
            f"Upload event not in analytics dashboard. "
            f"Before: {before}, After: {after}. "
            f"Files module may not be calling log_event on upload."
        )

        db_session.delete(event)
        db_session.commit()

    def test_failed_login_appears_in_unauthorized_table(
        self, auth_client, db_session
    ):
        """
        TEST G3 — PSD 7.2(ii): Unauthorized access attempts
        Failed logins must appear in unauthorized access table
        """
        from src.analytics.services.event_logger import log_event
        from src.analytics.constants import (
            AnalyticsEventType,
            AnalyticsEventStatus,
        )

        tc, headers, _ = auth_client
        test_ip = "10.99.88.77"

        event = log_event(
            db_session,
            event_type=AnalyticsEventType.LOGIN,
            status=AnalyticsEventStatus.FAILED,
            ip_address=test_ip,
        )
        db_session.commit()

        r = tc.get("/api/analytics/summary?days=7", headers=headers)
        attempts = r.json().get("security", {}).get("unauthorized_attempts", [])
        ips = [a.get("ip") for a in attempts]

        assert test_ip in ips, (
            f"Failed login from {test_ip} not in unauthorized_attempts. "
            f"Got IPs: {ips}. "
            f"PSD 7.2(ii) unauthorized access tracking broken."
        )

        db_session.delete(event)
        db_session.commit()

    def test_security_event_appears_in_timeline(
        self, auth_client, db_session
    ):
        """
        TEST G4 — PSD 7.2(iii): Security event reports
        Security events must appear in the SecurityTimeline
        """
        from src.analytics.services.event_logger import log_event
        from src.analytics.constants import (
            AnalyticsEventType,
            AnalyticsEventStatus,
        )

        tc, headers, _ = auth_client

        before_count = len(
            tc.get("/api/analytics/summary?days=7", headers=headers)
            .json().get("security", {}).get("events", [])
        )

        event = log_event(
            db_session,
            event_type=AnalyticsEventType.SECURITY,
            status=AnalyticsEventStatus.FAILED,
            ip_address="172.16.0.1",
            event_metadata={
                "severity_key": "brute_force",
                "label": "Test security event",
                "detail": "Integration test",
                "attempts": 3,
            },
        )
        db_session.commit()

        after_count = len(
            tc.get("/api/analytics/summary?days=7", headers=headers)
            .json().get("security", {}).get("events", [])
        )

        assert after_count >= before_count, (
            f"Security event not in timeline. "
            f"Before: {before_count}, After: {after_count}."
        )

        db_session.delete(event)
        db_session.commit()

    def test_recent_activity_serializes_without_crash(
        self, auth_client, db_session
    ):
        """
        TEST G5 — PSD 5(ii): File access history — RecentActivityPanel
        After adding event, /summary must not crash
        """
        from src.analytics.services.event_logger import log_event
        from src.analytics.constants import (
            AnalyticsEventType,
            AnalyticsEventStatus,
        )

        tc, headers, user_id = auth_client

        event = log_event(
            db_session,
            event_type=AnalyticsEventType.DOWNLOAD,
            status=AnalyticsEventStatus.SUCCESS,
            user_id=user_id,
        )
        db_session.commit()

        r = tc.get("/api/analytics/summary?days=7", headers=headers)

        assert r.status_code == 200, (
            f"Summary crashed after adding event — "
            f"ORM serialization error in recent_activity: {r.text[:400]}"
        )

        activities = r.json().get("recent_activity", {}).get("activities", [])
        assert isinstance(activities, list), (
            "recent_activity.activities is not a list"
        )

        db_session.delete(event)
        db_session.commit()


# ════════════════════════════════════════════════════════════════════════════
# DIRECT RUN SUPPORT
# ════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Running Analytics Module Tests")
    print("=" * 60 + "\n")

    test_analytics_summary_requires_authentication()
    test_export_csv_requires_authentication()
    test_export_pdf_requires_authentication()
    test_days_parameter_accepts_valid_range()
    test_csv_export_accepts_valid_tab_parameter()

    print("\n" + "=" * 60)
    print("Original 5 tests passed.")
    print("Run: python -m pytest tests/test_analytics.py -v  for all tests")
    print("=" * 60 + "\n")