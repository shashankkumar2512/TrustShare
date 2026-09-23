"""
oauth_config.py
Configures real OAuth2 clients for Google and Microsoft using the authlib library.
Reads client IDs and secrets from environment variables (set in .env).
"""
import os
from authlib.integrations.httpx_client import AsyncOAuth2Client

# ── Environment variables ──────────────────────────────────────────────────────
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/auth/oauth/google/callback")

MICROSOFT_CLIENT_ID = os.getenv("MICROSOFT_CLIENT_ID", "")
MICROSOFT_CLIENT_SECRET = os.getenv("MICROSOFT_CLIENT_SECRET", "")
MICROSOFT_TENANT_ID = os.getenv("MICROSOFT_TENANT_ID", "common")
MICROSOFT_REDIRECT_URI = os.getenv("MICROSOFT_REDIRECT_URI", "http://localhost:8000/api/auth/oauth/microsoft/callback")

# ── Google OAuth2 endpoints ────────────────────────────────────────────────────
GOOGLE_AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"
GOOGLE_SCOPES = "openid email profile"

# ── Microsoft OAuth2 endpoints ─────────────────────────────────────────────────
def get_ms_authorize_url():
    return f"https://login.microsoftonline.com/{MICROSOFT_TENANT_ID}/oauth2/v2.0/authorize"

def get_ms_token_url():
    return f"https://login.microsoftonline.com/{MICROSOFT_TENANT_ID}/oauth2/v2.0/token"

MICROSOFT_USERINFO_URL = "https://graph.microsoft.com/v1.0/me"
MICROSOFT_SCOPES = "openid email profile User.Read"


def make_google_client() -> AsyncOAuth2Client:
    """Create an authlib OAuth2 client configured for Google."""
    return AsyncOAuth2Client(
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        redirect_uri=GOOGLE_REDIRECT_URI,
        scope=GOOGLE_SCOPES,
    )


def make_microsoft_client() -> AsyncOAuth2Client:
    """Create an authlib OAuth2 client configured for Microsoft."""
    return AsyncOAuth2Client(
        client_id=MICROSOFT_CLIENT_ID,
        client_secret=MICROSOFT_CLIENT_SECRET,
        redirect_uri=MICROSOFT_REDIRECT_URI,
        scope=MICROSOFT_SCOPES,
    )
