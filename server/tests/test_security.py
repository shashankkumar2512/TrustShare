"""
Unit + Integration Tests for TrustShare Encryption & Security Module

Test Groups:
  - Original 20 tests (preserved exactly)
  - Group A: OTP Security Tests
  - Group B: Share Token Tests
  - Group C: Rate Limiter Tests (ISS-6)
  - Group D: Key Rotation DB Config (ISS-5, ISS-10)
  - Group E: Activity Logger Tests (ISS-4, ISS-15)
  - Group F: Security Controller Tests (ISS-11, ISS-12)
  - Group G: PSD Compliance Tests

Scope: Only server/src/security/ module
Teammate issues (auth, shares) reported separately.

Run: python -m pytest tests/test_security.py -v --tb=short
"""

import os
import pytest
import secrets as secrets_module
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
load_dotenv()

from src.security.encryption import (
    encrypt_bytes, decrypt_bytes, validate_key,
    generate_aad, AES_256_KEY_SIZE_BYTES, GCM_NONCE_SIZE_BYTES,
)
from src.security.key_manager import (
    generate_key, save_key, load_key, delete_key, key_exists,
)
from src.security.hashing import (
    calculate_sha256_bytes, compare_hashes, is_valid_sha256_hash,
)
from src.security.token_generator import (
    generate_share_token, generate_otp, generate_signed_token,
    verify_signed_token, compare_tokens, is_token_expired,
    SHARE_TOKEN_LENGTH_BYTES,
)
from src.security.key_rotation import (
    should_rotate, days_until_rotation, KEY_ROTATION_DAYS,
)
from src.security.exceptions import (
    EncryptionError, DecryptionError, KeyManagementError, IntegrityError,
)


# ════════════════════════════════════════════════════════════════════════════
# ORIGINAL TESTS (1–20) — Preserved exactly
# ════════════════════════════════════════════════════════════════════════════

class TestEncryption:
    """Tests for AES-256-GCM encryption module."""

    def test_encryption_decryption_roundtrip(self):
        """TEST 1: Verify data can be encrypted and decrypted correctly."""
        key           = os.urandom(AES_256_KEY_SIZE_BYTES)
        original_data = b"This is confidential TrustShare data!"
        encrypted     = encrypt_bytes(original_data, key)
        decrypted     = decrypt_bytes(encrypted, key)
        assert decrypted == original_data
        assert len(encrypted) > len(original_data)
        print("✅ TEST 1 PASSED: Encryption round-trip works")

    def test_encryption_rejects_invalid_key_size(self):
        """TEST 2: Verify AES-256 enforces 32-byte key."""
        data         = b"test data"
        invalid_keys = [b"short", os.urandom(16), os.urandom(24), os.urandom(33), b""]
        for key in invalid_keys:
            with pytest.raises(EncryptionError):
                encrypt_bytes(data, key)
        print("✅ TEST 2 PASSED: Invalid key sizes properly rejected")

    def test_encryption_detects_tampering(self):
        """TEST 3: Verify GCM authentication catches tampered data."""
        key       = os.urandom(AES_256_KEY_SIZE_BYTES)
        data      = b"important data"
        encrypted = encrypt_bytes(data, key)
        tampered  = bytearray(encrypted)
        tampered[-1] = tampered[-1] ^ 0xFF
        with pytest.raises(DecryptionError):
            decrypt_bytes(bytes(tampered), key)
        print("✅ TEST 3 PASSED: Tampered data properly detected")

    def test_encryption_wrong_key_fails(self):
        """TEST 4: Verify wrong key cannot decrypt data."""
        key1 = os.urandom(AES_256_KEY_SIZE_BYTES)
        key2 = os.urandom(AES_256_KEY_SIZE_BYTES)
        data = b"secret data"
        encrypted = encrypt_bytes(data, key1)
        with pytest.raises(DecryptionError):
            decrypt_bytes(encrypted, key2)
        print("✅ TEST 4 PASSED: Wrong key properly rejected")

    def test_encryption_with_aad(self):
        """TEST 5: Verify Associated Authenticated Data (AAD) works."""
        key       = os.urandom(AES_256_KEY_SIZE_BYTES)
        data      = b"contextual data"
        aad       = generate_aad(file_id=123, owner=456)
        encrypted = encrypt_bytes(data, key, aad=aad)
        decrypted = decrypt_bytes(encrypted, key, aad=aad)
        assert decrypted == data
        wrong_aad = generate_aad(file_id=999, owner=999)
        with pytest.raises(DecryptionError):
            decrypt_bytes(encrypted, key, aad=wrong_aad)
        print("✅ TEST 5 PASSED: AAD context binding works")


class TestKeyManagement:
    """Tests for key generation and management."""

    def test_key_generation_produces_correct_size(self):
        """TEST 6: Verify generated keys are exactly 32 bytes."""
        for _ in range(10):
            key = generate_key()
            assert isinstance(key, bytes)
            assert len(key) == AES_256_KEY_SIZE_BYTES
        print("✅ TEST 6 PASSED: All generated keys are correct size")

    def test_key_generation_produces_unique_keys(self):
        """TEST 7: Verify each generated key is unique."""
        keys = set()
        for _ in range(100):
            key = generate_key()
            keys.add(key)
        assert len(keys) == 100
        print("✅ TEST 7 PASSED: Key generation produces unique keys")

    def test_key_save_load_cycle(self):
        """TEST 8: Key save/load cycle."""
        test_file_id = "test_key_lifecycle_12345"
        original_key = generate_key()
        try:
            save_key(test_file_id, original_key)
            assert key_exists(test_file_id)
            loaded_key = load_key(test_file_id)
            assert loaded_key == original_key
            assert len(loaded_key) == AES_256_KEY_SIZE_BYTES
            print("✅ TEST 8 PASSED: Key save/load cycle works")
        finally:
            if key_exists(test_file_id):
                delete_key(test_file_id)


class TestHashing:
    """Tests for SHA-256 hashing and comparison."""

    def test_sha256_produces_correct_hash(self):
        """TEST 9: Verify SHA-256 produces known correct hash."""
        data          = b""
        expected_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        actual_hash   = calculate_sha256_bytes(data)
        assert actual_hash == expected_hash
        assert len(actual_hash) == 64
        assert is_valid_sha256_hash(actual_hash)
        print("✅ TEST 9 PASSED: SHA-256 hashing is correct")

    def test_timing_safe_hash_comparison(self):
        """TEST 10: Verify timing-safe hash comparison."""
        hash1 = calculate_sha256_bytes(b"data1")
        hash2 = calculate_sha256_bytes(b"data2")
        hash3 = calculate_sha256_bytes(b"data1")
        assert compare_hashes(hash1, hash3) == True
        assert compare_hashes(hash1, hash2) == False
        assert compare_hashes(hash1.upper(), hash1.lower()) == True
        assert compare_hashes(None, hash1) == False
        assert compare_hashes("", hash1) == False
        print("✅ TEST 10 PASSED: Timing-safe hash comparison works")


class TestTokenGeneration:
    """Tests for secure token generation."""

    def test_share_tokens_are_unique(self):
        """TEST 11: Verify share tokens are cryptographically unique."""
        tokens = set()
        for _ in range(1000):
            token = generate_share_token()
            tokens.add(token)
        assert len(tokens) == 1000
        for token in list(tokens)[:5]:
            assert len(token) == 43
        print("✅ TEST 11 PASSED: Share tokens are unique and correct length")

    def test_otp_generation(self):
        """TEST 12: Verify OTP generation produces valid numeric codes."""
        otp = generate_otp()
        assert len(otp) == 6
        assert otp.isdigit()
        for length in [4, 5, 6, 8]:
            otp = generate_otp(length=length)
            assert len(otp) == length
            assert otp.isdigit()
        otps = {generate_otp() for _ in range(100)}
        assert len(otps) > 50
        with pytest.raises(KeyManagementError):
            generate_otp(length=3)
        with pytest.raises(KeyManagementError):
            generate_otp(length=11)
        print("✅ TEST 12 PASSED: OTP generation works correctly")

    def test_signed_token_verification(self):
        """TEST 13: Verify signed tokens with HMAC and expiration."""
        secret       = os.urandom(32)
        wrong_secret = os.urandom(32)
        payload      = "user:123:file:456"
        token        = generate_signed_token(payload, secret, ttl_seconds=300)
        assert token is not None
        assert isinstance(token, str)
        result = verify_signed_token(token, secret)
        assert result['valid']             == True
        assert result['expired']           == False
        assert result['payload']           == payload
        assert result['remaining_seconds'] > 0
        wrong_result = verify_signed_token(token, wrong_secret)
        assert wrong_result['valid'] == False
        assert compare_tokens(token, token)       == True
        assert compare_tokens(token, "different") == False
        print("✅ TEST 13 PASSED: Signed token verification works")


class TestKeyRotation:
    """Tests for key rotation policies."""

    def test_rotation_policy_thresholds(self):
        """TEST 14: Verify rotation policy correctly identifies old keys."""
        now       = datetime.now(timezone.utc)
        fresh     = now - timedelta(days=1)
        threshold = now - timedelta(days=90)
        old       = now - timedelta(days=100)
        assert should_rotate(fresh)     == False
        assert should_rotate(threshold) == True
        assert should_rotate(old)       == True
        assert should_rotate(None)      == True
        custom_old = now - timedelta(days=31)
        assert should_rotate(custom_old, rotation_days=30) == True
        assert should_rotate(fresh, rotation_days=30)      == False
        print("✅ TEST 14 PASSED: Rotation policy correctly enforced")

    def test_days_until_rotation_calculation(self):
        """TEST 15: Verify days until rotation is calculated correctly."""
        now = datetime.now(timezone.utc)
        thirty_days_old = now - timedelta(days=30)
        assert 55 <= days_until_rotation(thirty_days_old) <= 60
        eighty_days_old = now - timedelta(days=80)
        assert 5 <= days_until_rotation(eighty_days_old) <= 10
        ninety_one_days = now - timedelta(days=91)
        assert days_until_rotation(ninety_one_days) < 0
        print("✅ TEST 15 PASSED: Rotation countdown calculated correctly")


class TestPasswordValidator:
    """Tests for password strength validation."""

    def test_weak_password_rejected(self):
        """TEST 16: Common weak passwords must be rejected."""
        from src.security.password_validator import validate_password
        weak_passwords = ["password", "123456", "admin", "qwerty"]
        for pwd in weak_passwords:
            result = validate_password(pwd)
            assert result.is_valid == False
            assert result.score    < 30
        print("✅ TEST 16 PASSED: Weak passwords properly rejected")

    def test_strong_password_accepted(self):
        """TEST 17: Strong passwords must be accepted with high score."""
        from src.security.password_validator import validate_password
        result = validate_password("MySecure!P@ssw0rd2024")
        assert result.is_valid    == True
        assert result.score       >= 70
        assert len(result.issues) == 0
        print("✅ TEST 17 PASSED: Strong passwords properly accepted")

    def test_password_checks_all_requirements(self):
        """TEST 18: Password validator checks all requirement types."""
        from src.security.password_validator import validate_password
        result = validate_password("aa")
        assert result.is_valid == False
        assert result.meets_requirements['min_length']    == False
        assert result.meets_requirements['has_uppercase'] == False
        assert result.meets_requirements['has_digit']     == False
        print("✅ TEST 18 PASSED: All requirement types checked")


class TestConfigLoader:
    """Tests for DB-driven configuration loader."""

    def test_config_returns_safe_defaults(self):
        """TEST 19: Config loader returns valid values."""
        from src.security.config_loader import get_config, get_config_int
        result  = get_config_int("NON_EXISTENT_KEY_12345", default=42)
        assert result == 42
        algo    = get_config("ENCRYPTION_ALGORITHM")
        assert isinstance(algo, str)
        missing = get_config("TOTALLY_MISSING_KEY", default="fallback")
        assert missing == "fallback"
        print("✅ TEST 19 PASSED: Config loader defaults work")

    def test_config_json_parsing(self):
        """TEST 20: Config loader correctly parses JSON values."""
        from src.security.config_loader import get_config_json, get_config_bool
        rate_limits = get_config_json("RATE_LIMITS")
        assert isinstance(rate_limits, dict)
        assert "default" in rate_limits
        passwords = get_config_json("COMMON_PASSWORDS")
        assert isinstance(passwords, list)
        assert len(passwords) > 0
        mongo = get_config_bool("MONGODB_ENABLED")
        assert isinstance(mongo, bool)
        print("✅ TEST 20 PASSED: JSON config parsing works")


# ════════════════════════════════════════════════════════════════════════════
# GROUP A — OTP Security Tests
# ════════════════════════════════════════════════════════════════════════════

class TestOTPSecurity:
    """
    Tests for OTP generation in token_generator.py (security module).
    PSD 4.ix: Secure Token Generation.
    """

    def test_otp_uses_cryptographic_randomness(self):
        """
        TEST A1 — PSD 4.ix: Secure Token Generation
        generate_otp() from token_generator must use secrets module.
        Verify by distribution spread across full range.
        """
        otps = [generate_otp() for _ in range(1000)]

        for otp in otps:
            assert len(otp) == 6,    f"OTP '{otp}' must be 6 digits"
            assert otp.isdigit(),    f"OTP '{otp}' must be numeric"

        otp_ints = [int(otp) for otp in otps]
        spread   = max(otp_ints) - min(otp_ints)

        assert spread > 100000, (
            f"OTP distribution too narrow ({spread}) — "
            f"may not be cryptographically random"
        )

    def test_otp_is_numeric_string(self):
        """TEST A2 — OTP must be exactly 6-digit numeric string."""
        for _ in range(50):
            otp = generate_otp()
            assert isinstance(otp, str), "OTP must be string type"
            assert otp.isdigit(),        "OTP must contain only digits"
            assert len(otp) == 6,        "OTP must be exactly 6 digits"

    def test_otp_uniqueness_rate(self):
        """TEST A3 — PSD 4.ix: Majority of OTPs must be unique."""
        otps         = [generate_otp() for _ in range(500)]
        unique_count = len(set(otps))
        assert unique_count >= 490, (
            f"Only {unique_count}/500 OTPs were unique — "
            f"randomness may be insufficient"
        )

    def test_token_generator_otp_uses_secrets(self):
        """
        TEST A4 — PSD 4.ix: Secure Token Generation
        Verify token_generator.py uses secrets module for OTP.
        """
        import inspect
        import src.security.token_generator as token_module

        source = inspect.getsource(token_module.generate_otp)

        assert "random.randint" not in source, (
            "token_generator.generate_otp must not use random.randint. "
            "Must use secrets module for cryptographic security."
        )
        assert "secrets" in source, (
            "token_generator.generate_otp must use secrets module. "
            "PSD 4.ix requires Secure Token Generation."
        )


# ════════════════════════════════════════════════════════════════════════════
# GROUP B — Share Token Security Tests
# ════════════════════════════════════════════════════════════════════════════

class TestShareTokenSecurity:
    """
    Tests for share token generation in token_generator.py.
    PSD 4.vi: Temporary Share Links, 4.ix: Secure Token Generation.
    """

    def test_share_token_is_256_bit(self):
        """TEST B1 — PSD 4.vi: Share token must be 256-bit (32 bytes)."""
        token = generate_share_token()
        assert len(token) == 43, (
            f"Share token is {len(token)} chars. "
            f"Expected 43 chars (256-bit)."
        )

    def test_share_token_length_bytes_constant(self):
        """TEST B2 — SHARE_TOKEN_LENGTH_BYTES must be 32 (256-bit)."""
        assert SHARE_TOKEN_LENGTH_BYTES == 32, (
            f"SHARE_TOKEN_LENGTH_BYTES is {SHARE_TOKEN_LENGTH_BYTES}. "
            f"Must be 32 (256-bit) per PSD Section 4.ix."
        )

    def test_share_token_high_entropy(self):
        """TEST B3 — Share tokens must have high entropy (all unique)."""
        tokens = [generate_share_token() for _ in range(500)]
        assert len(set(tokens)) == 500, (
            "All share tokens must be unique — "
            "collision indicates insufficient entropy"
        )

    def test_share_token_url_safe(self):
        """TEST B4 — Share tokens must only contain URL-safe characters."""
        unsafe_chars = set("+/=")
        for _ in range(100):
            token        = generate_share_token()
            found_unsafe = unsafe_chars.intersection(set(token))
            assert not found_unsafe, (
                f"Share token contains URL-unsafe chars: {found_unsafe}"
            )


# ════════════════════════════════════════════════════════════════════════════
# GROUP C — Rate Limiter DB Config Tests (ISS-6)
# ════════════════════════════════════════════════════════════════════════════

class TestRateLimiterConfig:
    """
    Tests verifying rate limiter uses correct DB column names.
    ISS-6: Wrong column names meant rate limits never loaded from DB.
    """

    def test_rate_limiter_allows_requests_within_limit(self):
        """TEST C1 — Rate limiter must allow requests within limit."""
        from src.security.rate_limiter import RateLimiter
        limiter   = RateLimiter()
        client_id = f"test_user_{secrets_module.token_hex(4)}"
        result    = limiter.check(client_id, "default")
        assert result["allowed"]   == True
        assert result["remaining"] >= 0

    def test_rate_limiter_blocks_after_limit(self):
        """TEST C2 — Rate limiter must block after limit exceeded."""
        from src.security.rate_limiter import RateLimiter
        limiter   = RateLimiter()
        client_id = f"test_spam_{secrets_module.token_hex(4)}"
        endpoint  = f"low_ep_{secrets_module.token_hex(4)}"   # unique per test

        # FIX: Use float('inf') so cache never expires during test
        limiter._config_cache     = {endpoint: {"requests": 3, "window_seconds": 60}}
        limiter._config_timestamp = float('inf')

        for i in range(3):
            result = limiter.check(client_id, endpoint)
            assert result["allowed"] == True, f"Request {i+1} should be allowed"

        result = limiter.check(client_id, endpoint)
        assert result["allowed"]   == False, "4th request should be blocked"
        assert result["remaining"] == 0
        assert result["reset_in"]  > 0

    def test_rate_limiter_uses_correct_column_names(self):
        """
        TEST C3 — ISS-6 Fix verification
        Rate limiter must use config_key and config_value not key and value.
        """
        import inspect
        from src.security.rate_limiter import RateLimiter

        source = inspect.getsource(RateLimiter._get_config)

        assert "AppConfig.key ==" not in source and \
               ".filter(AppConfig.key" not in source, (
            "DEFECT ISS-6: Rate limiter uses AppConfig.key — "
            "correct column name is AppConfig.config_key."
        )
        assert "config_key"   in source, "Must use AppConfig.config_key"
        assert "config_value" in source, "Must use .config_value attribute"

    def test_rate_limiter_different_clients_independent(self):
        """TEST C4 — Different clients must have independent rate limits."""
        from src.security.rate_limiter import RateLimiter
        limiter  = RateLimiter()
        endpoint = f"ind_ep_{secrets_module.token_hex(4)}"   # unique per test
        client_a = f"client_a_{secrets_module.token_hex(4)}"
        client_b = f"client_b_{secrets_module.token_hex(4)}"

        limiter._config_cache     = {endpoint: {"requests": 2, "window_seconds": 60}}
        limiter._config_timestamp = float('inf')

        limiter.check(client_a, endpoint)
        limiter.check(client_a, endpoint)
        blocked = limiter.check(client_a, endpoint)
        assert blocked["allowed"] == False, "client_a must be blocked after 2 requests"

        result = limiter.check(client_b, endpoint)
        assert result["allowed"] == True, (
            "client_b should be unaffected by client_a's rate limit"
        )


# ════════════════════════════════════════════════════════════════════════════
# GROUP D — Key Rotation DB Config Tests (ISS-5, ISS-10)
# ════════════════════════════════════════════════════════════════════════════

class TestKeyRotationDBConfig:
    """
    Tests verifying key rotation reads policy from DB not hardcoded values.
    ISS-5: get_rotation_status used KEY_ROTATION_DAYS constant.
    ISS-10: rotate_expired_keys used hardcoded defaults.
    """

    def test_get_rotation_days_function_exists(self):
        """TEST D1 — _get_rotation_days() must exist and return int."""
        from src.security.key_rotation import _get_rotation_days
        assert callable(_get_rotation_days)
        result = _get_rotation_days()
        assert isinstance(result, int)
        assert result > 0

    def test_rotation_status_uses_db_config(self):
        """
        TEST D2 — ISS-5 Fix verification
        get_rotation_status() must call _get_rotation_days(db).
        """
        import inspect
        from src.security.key_rotation import get_rotation_status

        source = inspect.getsource(get_rotation_status)

        assert "_get_rotation_days" in source, (
            "DEFECT ISS-5: get_rotation_status must call _get_rotation_days(db). "
            "Fix: rotation_days = _get_rotation_days(db) at start of function."
        )

    def test_rotate_expired_keys_uses_db_config(self):
        """
        TEST D3 — ISS-10 Fix verification
        rotate_expired_keys() must use _get_rotation_days and _get_max_batch.
        """
        import inspect
        from src.security.key_rotation import rotate_expired_keys

        source = inspect.getsource(rotate_expired_keys)

        assert "_get_rotation_days" in source, (
            "DEFECT ISS-10: rotate_expired_keys must call _get_rotation_days(db). "
            "Fix: if rotation_days is None: rotation_days = _get_rotation_days(db)"
        )
        assert "_get_max_batch" in source, (
            "DEFECT ISS-10: rotate_expired_keys must call _get_max_batch(db). "
            "Fix: if max_batch is None: max_batch = _get_max_batch(db)"
        )

    def test_rotation_respects_custom_policy(self):
        """TEST D4 — Key rotation must respect custom rotation_days param."""
        now       = datetime.now(timezone.utc)
        old_key   = now - timedelta(days=45)
        fresh_key = now - timedelta(days=10)

        assert should_rotate(old_key,   rotation_days=30) == True
        assert should_rotate(old_key,   rotation_days=90) == False
        assert should_rotate(fresh_key, rotation_days=30) == False
        assert should_rotate(fresh_key, rotation_days=90) == False


# ════════════════════════════════════════════════════════════════════════════
# GROUP E — Activity Logger Tests (ISS-4, ISS-15)
# Note: MongoDB not used currently — PostgreSQL only in current setup
# ════════════════════════════════════════════════════════════════════════════

class TestActivityLogger:
    """
    Tests verifying activity_logger.py has MONGODB_COLLECTION at module level.
    ISS-4, ISS-15: MONGODB_COLLECTION was only inside a function → NameError.
    MongoDB not active in current PostgreSQL-only setup.
    """

    def test_activity_logger_imports_without_error(self):
        """
        TEST E1 — ISS-4 Fix verification
        activity_logger.py must import without NameError.
        MONGODB_COLLECTION must be defined at module level.
        """
        try:
            import src.security.activity_logger as m
            assert hasattr(m, 'MONGODB_COLLECTION'), (
                "DEFECT ISS-4: MONGODB_COLLECTION must be at module level. "
                "Fix: MONGODB_COLLECTION = os.getenv('MONGODB_COLLECTION', "
                "'security_activity_logs') after MONGODB_DB_NAME."
            )
        except NameError as e:
            pytest.fail(
                f"DEFECT ISS-4: activity_logger has NameError: {e}. "
                f"MONGODB_COLLECTION must be defined at module level."
            )

    def test_mongodb_collection_defined_at_module_level(self):
        """TEST E2 — ISS-4/ISS-15: MONGODB_COLLECTION must be module-level constant."""
        import src.security.activity_logger as activity_module

        assert hasattr(activity_module, 'MONGODB_COLLECTION'), (
            "DEFECT ISS-4: MONGODB_COLLECTION not at module level. "
            "Fix: Add MONGODB_COLLECTION = os.getenv('MONGODB_COLLECTION', "
            "'security_activity_logs') after MONGODB_DB_NAME line."
        )
        assert isinstance(activity_module.MONGODB_COLLECTION, str)
        assert len(activity_module.MONGODB_COLLECTION) > 0

    def test_is_mongodb_available_returns_bool(self):
        """
        TEST E3 — is_mongodb_available() must return bool.
        Returns False in current PostgreSQL-only setup — this is expected.
        """
        from src.security.activity_logger import is_mongodb_available
        result = is_mongodb_available()
        assert isinstance(result, bool)
        assert result == False, (
            "MongoDB is not configured in current PostgreSQL-only setup. "
            "False is the correct response — activity_logger falls back to PostgreSQL."
        )

    def test_get_activity_stats_never_raises(self):
        """TEST E4 — get_activity_stats() must return dict without raising."""
        from src.security.activity_logger import get_activity_stats
        result = get_activity_stats()
        assert isinstance(result, dict)
        assert "mongodb_available" in result

    def test_log_security_activity_without_mongodb(self):
        """
        TEST E5 — log_security_activity() must not raise without MongoDB.
        Falls back to PostgreSQL-only logging gracefully.
        """
        from src.security.activity_logger import log_security_activity
        try:
            result = log_security_activity(
                action="TEST_ACTION",
                user_id=None,
                level="info",
                metadata={"test": True},
                db=None,
            )
            assert isinstance(result, bool)
        except Exception as e:
            pytest.fail(
                f"log_security_activity raised unexpectedly "
                f"(should fail silently): {e}"
            )


# ════════════════════════════════════════════════════════════════════════════
# GROUP F — Security Controller Tests (ISS-11, ISS-12)
# ════════════════════════════════════════════════════════════════════════════

class TestSecurityControllerFixes:
    """
    Tests verifying controller uses dynamic values not hardcoded strings.
    ISS-11: Algorithm name hardcoded.
    ISS-12: KEY_ROTATION_DAYS hardcoded.
    """

    def test_metrics_endpoint_uses_algorithm_registry(self):
        """
        TEST F1 — ISS-11 Fix verification
        get_security_metrics() must use get_current_algorithm() not hardcoded string.
        """
        import inspect
        import src.security.controller as controller_module

        source = inspect.getsource(controller_module.get_security_metrics)

        assert 'encryption_algorithm="AES-256-GCM"' not in source, (
            "DEFECT ISS-11: get_security_metrics has hardcoded 'AES-256-GCM'. "
            "Fix: algo = get_current_algorithm(); "
            "encryption_algorithm=algo.name"
        )

    def test_info_endpoint_uses_db_rotation_days(self):
        """
        TEST F2 — ISS-12 Fix verification
        get_security_module_info() must read rotation days from DB.
        """
        import inspect
        import src.security.controller as controller_module

        source = inspect.getsource(controller_module.get_security_module_info)

        assert "_get_rotation_days" in source or "get_config_int" in source, (
            "DEFECT ISS-12: get_security_module_info must read rotation days "
            "from DB. Fix: Add db param + rotation_days = _get_rotation_days(db)"
        )

    def test_algorithm_registry_current_algorithm(self):
        """TEST F3 — Algorithm registry must return AES-256-GCM as current."""
        from src.security.algorithm_registry import (
            get_current_algorithm, CURRENT_VERSION,
        )
        algo = get_current_algorithm()
        assert algo.name          == "AES-256-GCM"
        assert algo.key_size_bits == 256
        assert algo.status        == "active"
        assert CURRENT_VERSION    == 1


# ════════════════════════════════════════════════════════════════════════════
# GROUP G — PSD Compliance Tests (end-to-end)
# ════════════════════════════════════════════════════════════════════════════

class TestPSDCompliance:
    """
    End-to-end PSD compliance verification.
    PSD Section 4: Encryption & Security Module requirements.
    """

    def test_psd_4i_aes256_encryption(self):
        """TEST G1 — PSD 4.i: AES-256 Encryption."""
        assert AES_256_KEY_SIZE_BYTES == 32
        key       = generate_key()
        data      = b"PSD compliance test data"
        encrypted = encrypt_bytes(data, key)
        decrypted = decrypt_bytes(encrypted, key)
        assert decrypted == data

    def test_psd_4i_unique_key_per_file(self):
        """TEST G2 — PSD 4.Key.i: Unique encryption key per file."""
        keys        = [generate_key() for _ in range(50)]
        unique_keys = set(keys)
        assert len(unique_keys) == 50, (
            "PSD 4.Key.i: Every file must have a unique encryption key."
        )

    def test_psd_4ix_secure_token_generation(self):
        """TEST G3 — PSD 4.ix: All token types use secure generation."""
        from src.security.token_generator import (
            generate_share_token, generate_session_token,
            generate_csrf_token, generate_reset_token, generate_api_secret,
        )
        tokens = [
            generate_share_token(),
            generate_session_token(),
            generate_csrf_token(),
            generate_reset_token(),
            generate_api_secret(),
        ]
        for token in tokens:
            assert isinstance(token, str)
            assert len(token) >= 16
        assert len(set(tokens)) == len(tokens)

    def test_psd_4_authentication_tag_verification(self):
        """
        TEST G4 — PSD 4.i: AES-256-GCM authentication tag verification.
        """
        key      = generate_key()
        data     = b"authenticated data"
        ct       = encrypt_bytes(data, key)
        tampered = bytearray(ct)
        tampered[15] ^= 0x01

        with pytest.raises(DecryptionError):
            decrypt_bytes(bytes(tampered), key)

    def test_psd_section5_download_tracking(self):
        """TEST G5 — PSD 5.i: Download tracking via event logger."""
        from src.analytics.services.event_logger import log_event
        from src.analytics.constants import (
            AnalyticsEventType, AnalyticsEventStatus,
        )
        from src.database.core import SessionLocal

        db = SessionLocal()
        try:
            from src.analytics.models.analytics_event import AnalyticsEvent
            event = log_event(
                db,
                event_type=AnalyticsEventType.DOWNLOAD,
                status=AnalyticsEventStatus.SUCCESS,
                ip_address="127.0.0.1",
            )
            db.commit()
            assert event is not None
            assert event.event_type == AnalyticsEventType.DOWNLOAD
            db.delete(event)
            db.commit()
        finally:
            db.close()

    def test_psd_4vi_temporary_share_links(self):
        """TEST G6 — PSD 4.vi: Share tokens must be high entropy."""
        token    = generate_share_token()
        url_safe = set(
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
        )
        assert len(token) >= 40
        assert not set(token) - url_safe

    def test_psd_key_rotation_policy(self):
        """TEST G7 — PSD 4.Key.iv: Key rotation configurable from DB."""
        from src.security.key_rotation import _get_rotation_days
        days = _get_rotation_days()
        assert isinstance(days, int)
        assert 0 < days <= 365

    def test_psd_encryption_integrity_verification(self):
        """TEST G8 — PSD: SHA-256 integrity verification end-to-end."""
        import hashlib
        data          = b"File content for integrity check"
        upload_hash   = hashlib.sha256(data).hexdigest()
        key           = generate_key()
        encrypted     = encrypt_bytes(data, key)
        decrypted     = decrypt_bytes(encrypted, key)
        download_hash = hashlib.sha256(decrypted).hexdigest()
        assert upload_hash == download_hash
        stored_hash    = calculate_sha256_bytes(data)
        retrieved_hash = calculate_sha256_bytes(decrypted)
        assert compare_hashes(stored_hash, retrieved_hash) == True


# ════════════════════════════════════════════════════════════════════════════
# DIRECT RUN SUPPORT
# ════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("🔐 TRUSTSHARE ENCRYPTION & SECURITY — Test Suite")
    print("=" * 70)
    print("Scope: server/src/security/ module only")
    print("Teammate issues (auth, shares) reported separately")
    print("=" * 70 + "\n")
    pytest.main([__file__, "-v", "--tb=short"])