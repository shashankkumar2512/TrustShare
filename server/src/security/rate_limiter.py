"""
Rate Limiting Module — TrustShare Security

Configurable rate limiting for security-sensitive endpoints.
Prevents brute force attacks and API abuse.

Configuration loaded from database (no hardcoding).
Falls back to safe defaults if DB unavailable.

FIX ISS-4: Corrected DB column names from AppConfig.key/.value
to AppConfig.config_key/.config_value (matching the actual model).

References:
- OWASP Rate Limiting Cheat Sheet
- PRD: Secure file processing
"""

import os
import time
import json
import logging
from typing import Optional, Dict
from collections import defaultdict
from threading import Lock
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# CONFIGURATION (defaults — override from DB)

DEFAULT_RATE_LIMITS = {
    "security_health":   {"requests": 30, "window_seconds": 60},
    "rotate_keys":       {"requests": 5,  "window_seconds": 300},
    "validate_password": {"requests": 20, "window_seconds": 60},
    "verify_file":       {"requests": 10, "window_seconds": 60},
    "suggest_password":  {"requests": 15, "window_seconds": 60},
    "audit_log":         {"requests": 20, "window_seconds": 60},
    "performance":       {"requests": 30, "window_seconds": 60},
    "default":           {"requests": 60, "window_seconds": 60},
    "verify_file":       {"requests": 10, "window_seconds": 60},
    "suggest_password":  {"requests": 15, "window_seconds": 60},
    "audit_log":         {"requests": 20, "window_seconds": 60},
    "performance":       {"requests": 30, "window_seconds": 60},
    # Summary generation / regeneration endpoint
    "file_summary":      {"requests": 5,  "window_seconds": 60},
    "assistant_chat":            {"requests": 20, "window_seconds": 60},
    "assistant_test_connection": {"requests": 5,  "window_seconds": 60},
    "assistant_admin_update":    {"requests": 30, "window_seconds": 60},
    "default":           {"requests": 60, "window_seconds": 60},
}

__all__ = [
    'RateLimiter',
    'check_rate_limit',
    'get_rate_limit_status',
    'get_rate_limits_config',
]


class RateLimiter:
    """
    Thread-safe in-memory rate limiter with sliding window.

    For production: Replace with Redis-based rate limiter.
    """

    def __init__(self):
        self._lock             = Lock()
        self._requests: Dict[str, list] = defaultdict(list)
        self._config_cache     = None
        self._config_timestamp = 0
        self._CONFIG_TTL       = 300  # Refresh config every 5 mins

    def _get_config(self, endpoint: str, db=None) -> dict:
        """
        Get rate limit config from in-memory cache, DB, or defaults.

        Priority:
          1. In-memory cache (checked first — allows test injection)
          2. Database (loaded if cache is stale and db is available)
          3. DEFAULT_RATE_LIMITS (always the final fallback)
        """
        # FIX: Always check in-memory cache first regardless of db
        # This allows tests to inject config via _config_cache
        # and also serves cached DB values without needing db each call
        if self._config_cache and endpoint in self._config_cache:
            return self._config_cache[endpoint]

        # Try DB if available and cache is stale
        if db:
            try:
                now = time.time()
                if (
                    not self._config_cache
                    or (now - self._config_timestamp) > self._CONFIG_TTL
                ):
                    from src.security.models.app_config import AppConfig

                    config_row = (
                        db.query(AppConfig)
                        # FIX ISS-4: correct column name is config_key not key
                        .filter(AppConfig.config_key == "RATE_LIMITS")
                        .first()
                    )

                    # FIX ISS-4: correct attribute is config_value not value
                    if config_row and config_row.config_value:
                        self._config_cache     = json.loads(config_row.config_value)
                        self._config_timestamp = now
                        logger.debug("Rate limit config loaded from DB")

                # Check cache again after potential DB load
                if self._config_cache and endpoint in self._config_cache:
                    return self._config_cache[endpoint]

            except Exception as e:
                logger.warning(f"Failed to load rate limits from DB: {e}")

        # Final fallback to defaults
        return DEFAULT_RATE_LIMITS.get(endpoint, DEFAULT_RATE_LIMITS["default"])

    def check(
        self,
        client_id: str,
        endpoint:  str,
        db=None,
    ) -> dict:
        """
        Check if request should be rate limited.

        Args:
            client_id: Unique client identifier (user_id or IP).
            endpoint: Endpoint name for config lookup.
            db: Optional DB session for config.

        Returns:
            Dict with: allowed, remaining, reset_in, limit, window
        """
        config       = self._get_config(endpoint, db)
        max_requests = config["requests"]
        window       = config["window_seconds"]

        key    = f"{client_id}:{endpoint}"
        now    = time.time()
        cutoff = now - window

        with self._lock:
            # Remove expired entries
            self._requests[key] = [
                ts for ts in self._requests[key] if ts > cutoff
            ]

            current_count = len(self._requests[key])

            if current_count >= max_requests:
                oldest   = self._requests[key][0] if self._requests[key] else now
                reset_in = oldest + window - now

                logger.warning(
                    f"Rate limited: {client_id} on {endpoint} "
                    f"({current_count}/{max_requests})"
                )

                return {
                    "allowed":   False,
                    "remaining": 0,
                    "reset_in":  round(max(0, reset_in), 1),
                    "limit":     max_requests,
                    "window":    window,
                }

            # Allow and record
            self._requests[key].append(now)

            return {
                "allowed":   True,
                "remaining": max_requests - current_count - 1,
                "reset_in":  round(window, 1),
                "limit":     max_requests,
                "window":    window,
            }

    def get_status(self, client_id: str, endpoint: str, db=None) -> dict:
        """Get current rate limit status without consuming a request."""
        config       = self._get_config(endpoint, db)
        max_requests = config["requests"]
        window       = config["window_seconds"]

        key    = f"{client_id}:{endpoint}"
        now    = time.time()
        cutoff = now - window

        with self._lock:
            active = [
                ts for ts in self._requests.get(key, []) if ts > cutoff
            ]

            return {
                "endpoint":       endpoint,
                "limit":          max_requests,
                "window_seconds": window,
                "used":           len(active),
                "remaining":      max(0, max_requests - len(active)),
            }

    def reset(self, client_id: Optional[str] = None) -> None:
        """Reset rate limits."""
        with self._lock:
            if client_id:
                keys_to_remove = [
                    k for k in self._requests
                    if k.startswith(f"{client_id}:")
                ]
                for key in keys_to_remove:
                    del self._requests[key]
            else:
                self._requests.clear()


# GLOBAL INSTANCE

_limiter = RateLimiter()


def check_rate_limit(client_id: str, endpoint: str, db=None) -> dict:
    """Check rate limit for a client on an endpoint."""
    return _limiter.check(client_id, endpoint, db)


def get_rate_limit_status(client_id: str, endpoint: str, db=None) -> dict:
    """Get rate limit status without consuming a request."""
    return _limiter.get_status(client_id, endpoint, db)


def get_rate_limits_config() -> dict:
    """Get default rate limit configuration."""
    return DEFAULT_RATE_LIMITS.copy()
