"""
Automated tests for AI Assistant Module — Feature #19 + #20.

Coverage:
- Config service (encryption, caching, type casting)
- Function handlers (list_files, get_storage_info, etc.)
- Chat service (message flow, conversation management)
- Admin endpoints (config CRUD, connection test)
- User endpoints (status, chat, conversation history, rename)
- Security (authentication, admin-only access, conversation isolation)

Usage:
    cd server
    python -m pytest tests/test_assistant_service.py -v -s
"""

import pytest
import uuid
import json
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import text

from src.api import app
from src.database.core import SessionLocal
from src.entities.user import User
from src.entities.assistant_config import AssistantConfig
from src.entities.assistant_function import AssistantFunction
from src.entities.assistant_prompt import AssistantPrompt
from src.entities.assistant_suggested_query import AssistantSuggestedQuery
from src.entities.chat_conversation import ChatConversation
from src.entities.chat_message import ChatMessage
from src.auth.dependencies import hash_password, create_access_token

from src.assistant import config_service, functions
from src.assistant.encryption_helper import (
    encrypt_config_value,
    decrypt_config_value,
    is_encrypted,
    mask_secret,
)

client = TestClient(app)

# HELPERS


def get_db_session() -> Session:
    return SessionLocal()


def _hard_cleanup(db: Session, user_id: int):
    """Delete all FK-referencing rows first, then user."""
    child_tables = [
        "chat_messages",
        "chat_conversations",
        "analytics_events",
        "login_sessions",
        "notification_channel_preferences",
        "notification_preferences",
    ]

    for table in child_tables:
        try:
            if table == "chat_messages":
                db.execute(
                    text(
                        "DELETE FROM chat_messages WHERE conversation_id IN "
                        "(SELECT id FROM chat_conversations WHERE user_id = :uid)"
                    ),
                    {"uid": user_id},
                )
            else:
                db.execute(
                    text(f"DELETE FROM {table} WHERE user_id = :uid"), {"uid": user_id}
                )
            db.commit()
        except Exception:
            db.rollback()

    try:
        db.execute(text("DELETE FROM files WHERE owner_id = :uid"), {"uid": user_id})
        db.commit()
    except Exception:
        db.rollback()

    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            db.delete(user)
            db.commit()
    except Exception as e:
        print(f"[CLEANUP WARN] User {user_id}: {type(e).__name__}", flush=True)
        db.rollback()


def create_test_user(email: str, role: str = "member") -> User:
    db = get_db_session()
    try:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            _hard_cleanup(db, existing.id)

        user = User(
            name="Assistant Test User",
            email=email,
            hashed_password=hash_password("Test@1234"),
            role=role,
            plan="enterprise",
            is_active=True,
            storage_used=0,
            storage_quota=5 * 1024 * 1024 * 1024,  # 5 GB
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


# FIXTURES


@pytest.fixture
def test_user():
    email = f"asst_user_{uuid.uuid4().hex[:8]}@demo.com"
    user = create_test_user(email, role="member")
    yield user
    cleanup_user(email)


@pytest.fixture
def test_admin():
    email = f"asst_admin_{uuid.uuid4().hex[:8]}@demo.com"
    user = create_test_user(email, role="admin")
    yield user
    cleanup_user(email)


# ENCRYPTION HELPER TESTS


class TestEncryptionHelper:
    """Verifies config secret encryption/decryption."""

    def test_encrypt_creates_versioned_output(self):
        """Encrypted value should have enc_v1: prefix."""
        encrypted = encrypt_config_value("my_secret_key_123")
        assert encrypted.startswith("enc_v1:")
        assert len(encrypted) > len("enc_v1:")

    def test_encrypt_decrypt_round_trip(self):
        """Decrypting encrypted value should return original."""
        original = "gsk_abc123XYZ456"
        encrypted = encrypt_config_value(original)
        decrypted = decrypt_config_value(encrypted)
        assert decrypted == original

    def test_encrypt_produces_different_ciphertexts(self):
        """Same plaintext should produce different ciphertexts (random nonce)."""
        plain = "same_secret"
        enc1 = encrypt_config_value(plain)
        enc2 = encrypt_config_value(plain)
        assert enc1 != enc2  # different nonces
        assert decrypt_config_value(enc1) == decrypt_config_value(enc2) == plain

    def test_double_encrypt_returns_same_value(self):
        """Already-encrypted values should not be re-encrypted."""
        encrypted = encrypt_config_value("test")
        double_encrypted = encrypt_config_value(encrypted)
        assert encrypted == double_encrypted

    def test_decrypt_plain_value_returns_as_is(self):
        """Non-encrypted values should pass through decrypt unchanged."""
        plain = "not_encrypted"
        assert decrypt_config_value(plain) == plain

    def test_decrypt_none_returns_none(self):
        """None input should return None."""
        assert decrypt_config_value(None) is None

    def test_is_encrypted_detects_prefix(self):
        """Should correctly identify encrypted values."""
        assert is_encrypted("enc_v1:abc123") is True
        assert is_encrypted("plaintext") is False
        assert is_encrypted(None) is False
        assert is_encrypted("") is False

    def test_mask_secret_shows_last_chars(self):
        """Masking should show only last 4 chars by default."""
        result = mask_secret("gsk_1234567890abcd")
        assert result.endswith("abcd")
        assert "•" in result

    def test_mask_secret_returns_not_configured_for_empty(self):
        """Empty value should return 'Not configured'."""
        assert mask_secret(None) == "Not configured"
        assert mask_secret("") == "Not configured"


# CONFIG SERVICE TESTS


class TestConfigService:
    """Verifies DB config loading with type casting."""

    def test_get_bool_returns_true_for_true_string(self):
        db = get_db_session()
        try:
            # ENABLE_ASSISTANT should be seeded as "true"
            result = config_service.get_bool(db, "ENABLE_ASSISTANT", False)
            assert result is True
        finally:
            db.close()

    def test_get_int_casts_correctly(self):
        db = get_db_session()
        try:
            # LLM_MAX_TOKENS should be seeded as "1024"
            result = config_service.get_int(db, "LLM_MAX_TOKENS", 0)
            assert result == 1024
        finally:
            db.close()

    def test_get_float_casts_correctly(self):
        db = get_db_session()
        try:
            # LLM_TEMPERATURE should be seeded as "0.7"
            result = config_service.get_float(db, "LLM_TEMPERATURE", 0.0)
            assert result == 0.7
        finally:
            db.close()

    def test_get_str_returns_default_for_missing(self):
        db = get_db_session()
        try:
            result = config_service.get_str(db, "NONEXISTENT_KEY_XYZ", "fallback")
            assert result == "fallback"
        finally:
            db.close()

    def test_get_all_by_category_returns_llm_configs(self):
        db = get_db_session()
        try:
            items = config_service.get_all_by_category(db, "llm")
            # Should have at least LLM_PROVIDER, LLM_MODEL, LLM_API_KEY, etc.
            assert len(items) >= 5
            keys = [item["key"] for item in items]
            assert "LLM_MODEL" in keys
            assert "LLM_API_KEY" in keys
        finally:
            db.close()

    def test_secret_never_exposed_in_get_all(self):
        db = get_db_session()
        try:
            items = config_service.get_all_by_category(db, "llm")
            api_key_item = next((i for i in items if i["key"] == "LLM_API_KEY"), None)
            assert api_key_item is not None
            assert api_key_item["is_secret"] is True
            # value should be None (never expose actual secret)
            assert api_key_item["value"] is None
            # display_value should be masked
            assert (
                "•" in api_key_item["display_value"]
                or api_key_item["display_value"] == "Not configured"
            )
        finally:
            db.close()

    def test_set_value_encrypts_secret(self):
        db = get_db_session()
        try:
            # Set a secret value
            config_service.set_value(db, "LLM_API_KEY", "test_secret_key_abc")

            # Verify raw DB value is encrypted
            row = db.query(AssistantConfig).filter_by(config_key="LLM_API_KEY").first()
            assert row.config_value.startswith("enc_v1:")

            # But get() should return decrypted
            config_service.clear_cache()
            decrypted = config_service.get(db, "LLM_API_KEY")
            assert decrypted == "test_secret_key_abc"
        finally:
            db.close()


# FUNCTION HANDLER TESTS


class TestFunctionHandlers:
    """Verifies the 8 LLM-callable functions execute correctly."""

    def test_get_storage_info_returns_user_quota(self, test_user):
        db = get_db_session()
        try:
            result = functions.get_storage_info(db, test_user, {})
            assert "used" in result
            assert "quota" in result
            assert result["quota_bytes"] == 5 * 1024 * 1024 * 1024
            assert result["plan"] == "enterprise"
        finally:
            db.close()

    def test_get_user_profile_returns_correct_data(self, test_user):
        db = get_db_session()
        try:
            result = functions.get_user_profile(db, test_user, {})
            assert result["name"] == test_user.name
            assert result["email"] == test_user.email
            assert result["role"] == "member"
            assert result["plan"] == "enterprise"
        finally:
            db.close()

    def test_list_files_returns_empty_when_no_files(self, test_user):
        db = get_db_session()
        try:
            result = functions.list_files(db, test_user, {})
            assert result["total_matched"] == 0
            assert result["files"] == []
        finally:
            db.close()

    def test_list_files_respects_limit(self, test_user):
        """Even without files, limit param should be recognized."""
        db = get_db_session()
        try:
            result = functions.list_files(db, test_user, {"limit": 5})
            assert "filters_applied" in result
        finally:
            db.close()

    def test_search_files_requires_query(self, test_user):
        db = get_db_session()
        try:
            result = functions.search_files(db, test_user, {"query": ""})
            assert result["total_matched"] == 0
        finally:
            db.close()

    def test_get_notifications_returns_structure(self, test_user):
        db = get_db_session()
        try:
            result = functions.get_notifications(db, test_user, {})
            assert "total_matched" in result
            assert "notifications" in result
            assert isinstance(result["notifications"], list)
        finally:
            db.close()

    def test_list_active_sessions_returns_structure(self, test_user):
        db = get_db_session()
        try:
            result = functions.list_active_sessions(db, test_user, {})
            assert "total_sessions" in result
            assert "sessions" in result
        finally:
            db.close()

    def test_execute_function_handles_unknown_name(self, test_user):
        db = get_db_session()
        try:
            result = functions.execute_function(
                "nonexistent_function_xyz",
                {},
                db,
                test_user,
            )
            assert result.get("error") is True
        finally:
            db.close()

    def test_find_shares_returns_structure(self, test_user):
        db = get_db_session()
        try:
            result = functions.find_shares(db, test_user, {})
            assert "direct_shares" in result
            assert "share_links" in result
        finally:
            db.close()


# PUBLIC ENDPOINT TESTS (Non-Admin Users)


class TestPublicEndpoints:
    """Verifies user-facing endpoints work correctly."""

    def test_status_endpoint_returns_ui_config(self, test_user):
        headers = get_auth_header(test_user.id)
        r = client.get("/api/assistant/status", headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert "is_enabled" in data
        assert "is_configured" in data
        assert "bot_name" in data
        assert "max_message_length" in data

    def test_status_requires_authentication(self):
        r = client.get("/api/assistant/status")
        assert r.status_code == 401

    def test_suggestions_endpoint_returns_list(self, test_user):
        headers = get_auth_header(test_user.id)
        r = client.get("/api/assistant/suggestions", headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        # Should have seeded suggestions
        assert len(data) >= 1

    def test_conversations_list_empty_for_new_user(self, test_user):
        headers = get_auth_header(test_user.id)
        r = client.get("/api/assistant/conversations", headers=headers)
        assert r.status_code == 200
        assert r.json() == []

    def test_chat_requires_authentication(self):
        r = client.post("/api/assistant/chat", json={"message": "test"})
        assert r.status_code == 401


# CONVERSATION MANAGEMENT TESTS


class TestConversationManagement:
    """Verifies conversation isolation and CRUD."""

    def test_user_cannot_see_other_users_conversations(self, test_user):
        """Create conversation for another user, verify test_user can't see it."""
        # Create another user with conversations
        other_email = f"other_{uuid.uuid4().hex[:8]}@demo.com"
        other = create_test_user(other_email)

        try:
            db = get_db_session()
            try:
                conv = ChatConversation(
                    user_id=other.id,
                    title="Other user's chat",
                    message_count=1,
                )
                db.add(conv)
                db.commit()
            finally:
                db.close()

            # test_user should NOT see this conversation
            headers = get_auth_header(test_user.id)
            r = client.get("/api/assistant/conversations", headers=headers)
            assert r.status_code == 200
            titles = [c.get("title") for c in r.json()]
            assert "Other user's chat" not in titles
        finally:
            cleanup_user(other_email)

    def test_user_cannot_access_other_users_messages(self, test_user):
        """Attempting to fetch another user's messages should return 404."""
        other_email = f"other_{uuid.uuid4().hex[:8]}@demo.com"
        other = create_test_user(other_email)

        try:
            # Create conversation for other user
            db = get_db_session()
            try:
                conv = ChatConversation(
                    user_id=other.id, title="Private", message_count=0
                )
                db.add(conv)
                db.commit()
                db.refresh(conv)
                conv_id = conv.id
            finally:
                db.close()

            # test_user tries to access it
            headers = get_auth_header(test_user.id)
            r = client.get(
                f"/api/assistant/conversations/{conv_id}/messages",
                headers=headers,
            )
            assert r.status_code == 404
        finally:
            cleanup_user(other_email)

    def test_archive_conversation(self, test_user):
        # Create a conversation
        db = get_db_session()
        try:
            conv = ChatConversation(user_id=test_user.id, title="Test", message_count=0)
            db.add(conv)
            db.commit()
            db.refresh(conv)
            conv_id = conv.id
        finally:
            db.close()

        # Archive it
        headers = get_auth_header(test_user.id)
        r = client.delete(f"/api/assistant/conversations/{conv_id}", headers=headers)
        assert r.status_code == 204

        # Verify it's not in the list
        r2 = client.get("/api/assistant/conversations", headers=headers)
        ids = [c["id"] for c in r2.json()]
        assert conv_id not in ids

    def test_rename_conversation(self, test_user):
        # Create a conversation
        db = get_db_session()
        try:
            conv = ChatConversation(
                user_id=test_user.id, title="Old Title", message_count=0
            )
            db.add(conv)
            db.commit()
            db.refresh(conv)
            conv_id = conv.id
        finally:
            db.close()

        # Rename
        headers = get_auth_header(test_user.id)
        r = client.patch(
            f"/api/assistant/conversations/{conv_id}",
            headers=headers,
            json={"title": "New Awesome Title"},
        )
        assert r.status_code == 200
        assert r.json()["title"] == "New Awesome Title"

        # Verify persisted
        db = get_db_session()
        try:
            fresh = db.query(ChatConversation).filter_by(id=conv_id).first()
            assert fresh.title == "New Awesome Title"
        finally:
            db.close()

    def test_rename_rejects_other_users_conversation(self, test_user):
        other_email = f"other_{uuid.uuid4().hex[:8]}@demo.com"
        other = create_test_user(other_email)

        try:
            db = get_db_session()
            try:
                conv = ChatConversation(
                    user_id=other.id, title="Not mine", message_count=0
                )
                db.add(conv)
                db.commit()
                db.refresh(conv)
                conv_id = conv.id
            finally:
                db.close()

            headers = get_auth_header(test_user.id)
            r = client.patch(
                f"/api/assistant/conversations/{conv_id}",
                headers=headers,
                json={"title": "Hacked!"},
            )
            assert r.status_code == 404
        finally:
            cleanup_user(other_email)


# ADMIN ENDPOINT TESTS


class TestAdminEndpoints:
    """Verifies admin-only endpoints and access control."""

    def test_admin_can_list_configs(self, test_admin):
        headers = get_auth_header(test_admin.id)
        r = client.get("/api/assistant/admin/config", headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        categories = [g["category"] for g in data]
        assert "llm" in categories

    def test_non_admin_cannot_access_admin_config(self, test_user):
        headers = get_auth_header(test_user.id)
        r = client.get("/api/assistant/admin/config", headers=headers)
        assert r.status_code == 403

    def test_admin_can_update_config(self, test_admin):
        headers = get_auth_header(test_admin.id)
        r = client.put(
            "/api/assistant/admin/config/BOT_NAME",
            headers=headers,
            json={"value": "Test Bot Name"},
        )
        assert r.status_code == 200
        assert r.json()["status"] == "success"

        # Restore original
        client.put(
            "/api/assistant/admin/config/BOT_NAME",
            headers=headers,
            json={"value": "TrustShare Assistant"},
        )

    def test_admin_cannot_update_nonexistent_config(self, test_admin):
        headers = get_auth_header(test_admin.id)
        r = client.put(
            "/api/assistant/admin/config/NONEXISTENT_XYZ",
            headers=headers,
            json={"value": "test"},
        )
        assert r.status_code == 400

    def test_admin_can_bulk_update_configs(self, test_admin):
        headers = get_auth_header(test_admin.id)
        r = client.post(
            "/api/assistant/admin/config/bulk",
            headers=headers,
            json={
                "updates": {
                    "LLM_MAX_TOKENS": 2048,
                    "LLM_TEMPERATURE": 0.5,
                }
            },
        )
        assert r.status_code == 200
        assert r.json()["updated_count"] == 2

        # Restore
        client.post(
            "/api/assistant/admin/config/bulk",
            headers=headers,
            json={
                "updates": {
                    "LLM_MAX_TOKENS": 1024,
                    "LLM_TEMPERATURE": 0.7,
                }
            },
        )

    def test_get_models_returns_list(self, test_admin):
        headers = get_auth_header(test_admin.id)
        r = client.get("/api/assistant/admin/models", headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_admin_cache_clear(self, test_admin):
        headers = get_auth_header(test_admin.id)
        r = client.post("/api/assistant/admin/cache/clear", headers=headers)
        assert r.status_code == 200
        assert r.json()["status"] == "success"


# DATABASE SEED VERIFICATION


class TestSeededData:
    """Verifies startup seeders populated the DB correctly."""

    def test_configs_are_seeded(self):
        db = get_db_session()
        try:
            count = db.query(AssistantConfig).count()
            assert count >= 20, f"Expected at least 20 configs, got {count}"
        finally:
            db.close()

    def test_functions_are_seeded(self):
        db = get_db_session()
        try:
            count = db.query(AssistantFunction).count()
            assert count >= 8, f"Expected at least 8 functions, got {count}"

            # Verify specific ones exist
            expected = [
                "list_files",
                "search_files",
                "get_storage_info",
                "get_storage_breakdown",
                "find_shares",
                "get_user_profile",
                "list_active_sessions",
                "get_notifications",
            ]
            db_names = [f.function_name for f in db.query(AssistantFunction).all()]
            for name in expected:
                assert name in db_names, f"Missing seeded function: {name}"
        finally:
            db.close()

    def test_prompts_are_seeded(self):
        db = get_db_session()
        try:
            count = db.query(AssistantPrompt).count()
            assert count >= 7, f"Expected at least 7 prompts, got {count}"

            # Verify SYSTEM_PROMPT exists
            sys_prompt = (
                db.query(AssistantPrompt).filter_by(prompt_key="SYSTEM_PROMPT").first()
            )
            assert sys_prompt is not None
            assert len(sys_prompt.prompt_text) > 100
        finally:
            db.close()

    def test_suggested_queries_are_seeded(self):
        db = get_db_session()
        try:
            count = db.query(AssistantSuggestedQuery).count()
            assert count >= 10, f"Expected at least 10 queries, got {count}"
        finally:
            db.close()

    def test_llm_api_key_config_exists(self):
        """The LLM_API_KEY row must exist (even if unset)."""
        db = get_db_session()
        try:
            config = (
                db.query(AssistantConfig).filter_by(config_key="LLM_API_KEY").first()
            )
            assert config is not None
            assert config.is_secret is True
        finally:
            db.close()
