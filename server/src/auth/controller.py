from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from src.database.core import get_db
from src.auth import models, service
from src.auth.dependencies import (
    get_current_user,
    decode_token,
    create_access_token,
    create_refresh_token,
)
from src.entities.user import User
from src.entities.audit_log import AuditLog
from src.notifications.service import create_notification
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm

import secrets
import threading
from datetime import datetime, timedelta, timezone

_oauth_token_store: dict[str, dict] = {}
_oauth_store_lock = threading.Lock()


def _store_oauth_tokens(access_token: str, refresh_token: str) -> str:
    code = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=60)
    with _oauth_store_lock:
        _oauth_token_store[code] = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_at": expires_at,
        }
    return code


router = APIRouter()


def _get_client_ip(request: Request) -> str | None:
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


def _log_audit(db: Session, user_id: int | None, action: str, resource_name: str, ip_address: str | None, level: str = "info"):
    """Write to audit_logs table so events appear in the Activity page."""
    log = AuditLog(
        user_id=user_id,
        action=action,
        resource_type="user",
        resource_name=resource_name,
        ip_address=ip_address,
        level=level,
    )
    db.add(log)


@router.post("/login", response_model=models.TokenResponse)
def login(
    credentials: models.LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    ip = _get_client_ip(request)

    user = service.authenticate_user(
        db,
        credentials.email,
        credentials.password,
        ip_address=ip,
    )
    if not user:
        # Log failed login to audit_logs
        _log_audit(db, None, "LOGIN_FAILED", credentials.email, ip, "warn")
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if not user.is_active:
        _log_audit(db, user.id, "LOGIN_BLOCKED", user.email, ip, "error")
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account suspended",
        )

    if user.mfa_enabled:
        _log_audit(db, user.id, "LOGIN_MFA_PENDING", user.email, ip, "info")
        db.commit()
        return service.build_mfa_pending_response(user)

    response = service._build_token_response(user, db=db, request=request)

    # Log successful login to audit_logs
    _log_audit(db, user.id, "LOGIN_SUCCESS", user.email, ip, "info")

    create_notification(
        db,
        user_id=user.id,
        type="security",
        category="security",
        title="New login to your account",
        message=f"A successful sign-in from {ip or 'unknown location'}.",
        icon="security",
        commit=True,
    )
    return response


@router.post("/login/swagger", response_model=models.TokenResponse)
def swagger_login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    ip = _get_client_ip(request)

    user = service.authenticate_user(
        db,
        form_data.username,
        form_data.password,
        ip_address=ip,
    )

    if not user:
        _log_audit(db, None, "LOGIN_FAILED", form_data.username, ip, "warn")
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        _log_audit(db, user.id, "LOGIN_BLOCKED", user.email, ip, "error")
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account suspended",
        )

    response = service._build_token_response(user, db=db, request=request)

    _log_audit(db, user.id, "LOGIN_SUCCESS", user.email, ip, "info")

    create_notification(
        db,
        user_id=user.id,
        type="security",
        category="security",
        title="New login to your account",
        message="A successful sign-in to TrustShare was completed.",
        icon="security",
        commit=True,
    )
    return response


@router.post(
    "/signup",
    response_model=models.TokenResponse,
    status_code=status.HTTP_201_CREATED,
)
def signup(
    data: models.SignupRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    ip = _get_client_ip(request)
    return service.register_user(db, data, request=request, ip_address=ip)


@router.get("/me", response_model=models.UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/refresh", response_model=models.TokenResponse)
def refresh(
    body: models.RefreshRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    payload = decode_token(body.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    try:
        from src.entities.login_session import LoginSession
        active_session = db.query(LoginSession).filter(
            LoginSession.user_id == user.id,
            LoginSession.refresh_token == body.refresh_token,
            LoginSession.is_current == True,
        ).first()

        if not active_session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired or logged out. Please login again.",
            )

        active_session.is_current = False
        db.commit()

    except HTTPException:
        raise
    except Exception:
        pass

    return service._build_token_response(user, db=db, request=request)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        from src.entities.login_session import LoginSession
        db.query(LoginSession).filter(
            LoginSession.user_id == current_user.id,
            LoginSession.is_current == True,
        ).update({"is_current": False})
        db.commit()
    except Exception:
        db.rollback()
    return None


@router.post("/verify-otp", response_model=models.TokenResponse)
def verify_otp(
    body: models.VerifyOTPRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    ip = _get_client_ip(request)
    payload = decode_token(body.mfa_token)
    if payload.get("type") != "mfa_pending":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid MFA session token",
        )

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    if not service.verify_otp_code(user.id, body.code, db=db, ip_address=ip):
        _log_audit(db, user.id, "LOGIN_MFA_FAILED", user.email, ip, "warn")
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP code",
        )

    response = service._build_token_response(user, db=db, request=request)

    _log_audit(db, user.id, "LOGIN_SUCCESS", f"{user.email} (MFA)", ip, "info")

    create_notification(
        db,
        user_id=user.id,
        type="security",
        category="security",
        title="New login to your account",
        message="A successful MFA sign-in to TrustShare was completed.",
        icon="security",
        commit=True,
    )
    return response


@router.post("/resend-otp")
def resend_otp(body: models.ResendOTPRequest, db: Session = Depends(get_db)):
    payload = decode_token(body.mfa_token)
    if payload.get("type") != "mfa_pending":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid MFA session token",
        )

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    service.generate_otp(user.id, to_email=user.email, user_name=user.name)
    return {
        "status": "success",
        "message": "OTP resent to your registered email",
    }


@router.post("/forgot-password")
def forgot_password(
    body: models.ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    service.request_password_reset(db, body.email)
    return {
        "status": "success",
        "message": "Password reset link generated if email exists",
    }


@router.post("/reset-password")
def reset_password(
    body: models.ResetPasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    ip = _get_client_ip(request)
    service.reset_password_in_db(
        db,
        body.token,
        body.new_password,
        ip_address=ip,
    )
    return {"status": "success", "message": "Password reset successfully"}


import os
from src.auth.oauth_config import (
    make_google_client,
    make_microsoft_client,
    GOOGLE_AUTHORIZE_URL,
    GOOGLE_TOKEN_URL,
    GOOGLE_USERINFO_URL,
    GOOGLE_REDIRECT_URI,
    get_ms_authorize_url,
    get_ms_token_url,
    MICROSOFT_USERINFO_URL,
    MICROSOFT_REDIRECT_URI,
)

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


@router.get("/oauth/google")
async def google_login():
    client = make_google_client()
    uri, state = client.create_authorization_url(GOOGLE_AUTHORIZE_URL)
    return RedirectResponse(url=uri)


@router.get("/oauth/google/callback")
async def google_callback(
    code: str,
    request: Request,
    db: Session = Depends(get_db),
):
    ip = _get_client_ip(request)
    client = make_google_client()

    token = await client.fetch_token(
        GOOGLE_TOKEN_URL,
        code=code,
        redirect_uri=GOOGLE_REDIRECT_URI,
    )

    resp = await client.get(GOOGLE_USERINFO_URL)
    profile = resp.json()

    google_email = profile.get("email")
    google_name = profile.get("name", google_email)

    if not google_email:
        raise HTTPException(
            status_code=400,
            detail="Google did not return an email address",
        )

    user = service.get_or_create_oauth_user(
        db, "google", google_email, google_name, ip_address=ip,
    )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account suspended",
        )

    token_resp = service._build_token_response(user, db=db, request=request)

    exchange_code = _store_oauth_tokens(
        token_resp.access_token,
        token_resp.refresh_token,
    )
    redirect_url = f"{FRONTEND_URL}/oauth-callback?code={exchange_code}&provider=google"
    return RedirectResponse(url=redirect_url)


@router.get("/oauth/microsoft")
async def microsoft_login():
    client = make_microsoft_client()
    uri, state = client.create_authorization_url(get_ms_authorize_url())
    return RedirectResponse(url=uri)


@router.get("/oauth/microsoft/callback")
async def microsoft_callback(
    code: str,
    request: Request,
    db: Session = Depends(get_db),
):
    ip = _get_client_ip(request)
    client = make_microsoft_client()

    token = await client.fetch_token(
        get_ms_token_url(),
        code=code,
        redirect_uri=MICROSOFT_REDIRECT_URI,
    )

    resp = await client.get(MICROSOFT_USERINFO_URL)
    profile = resp.json()

    ms_email = profile.get("mail") or profile.get("userPrincipalName")
    ms_name = profile.get("displayName", ms_email)

    if not ms_email:
        raise HTTPException(
            status_code=400,
            detail="Microsoft did not return an email address",
        )

    user = service.get_or_create_oauth_user(
        db, "microsoft", ms_email, ms_name, ip_address=ip,
    )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account suspended",
        )

    token_resp = service._build_token_response(user, db=db, request=request)

    exchange_code = _store_oauth_tokens(
        token_resp.access_token,
        token_resp.refresh_token,
    )
    redirect_url = f"{FRONTEND_URL}/oauth-callback?code={exchange_code}&provider=microsoft"
    return RedirectResponse(url=redirect_url)


@router.post("/oauth/exchange")
def oauth_exchange(body: models.OAuthExchangeRequest):
    with _oauth_store_lock:
        entry = _oauth_token_store.pop(body.code, None)

    if not entry:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired OAuth exchange code",
        )

    if datetime.now(timezone.utc) > entry["expires_at"]:
        raise HTTPException(
            status_code=400,
            detail="OAuth exchange code has expired. Please login again.",
        )

    return {
        "access_token": entry["access_token"],
        "refresh_token": entry["refresh_token"],
        "token_type": "bearer",
    }


@router.post("/mfa/setup")
def mfa_setup(
    current_user: User = Depends(get_current_user),
):
    if current_user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is already enabled",
        )
    service.generate_otp(
        current_user.id,
        to_email=current_user.email,
        user_name=current_user.name,
    )
    return {
        "status": "otp_sent",
        "message": "Verification code sent to your registered email",
    }


@router.post("/mfa/verify-setup", response_model=models.UserOut)
def mfa_verify_setup(
    body: models.VerifyMFASetupRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is already enabled",
        )
    if not service.verify_otp_code(current_user.id, body.code, db=db):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification code",
        )
    return service.enable_mfa(db, current_user)


@router.post("/mfa/disable-with-password", response_model=models.UserOut)
def mfa_disable_with_password(
    body: models.DisableMFARequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from src.auth.dependencies import verify_password
    if not verify_password(body.password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect password",
        )
    return service.disable_mfa(db, current_user)


@router.post("/change-password")
def change_password(
    body: models.ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service.change_password(db, current_user, body.current_password, body.new_password)
    return {"status": "success", "message": "Password changed successfully"}


from sqlalchemy import func
from src.entities.file import File


@router.get("/me/storage-breakdown")
def storage_breakdown(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    files = (
        db.query(File.mimetype, File.size)
        .filter(
            File.owner_id == current_user.id,
            File.is_deleted == False,
        )
        .all()
    )

    categories = {
        "documents": {"size": 0, "count": 0, "color": "#3b82f6"},
        "media":     {"size": 0, "count": 0, "color": "#8b5cf6"},
        "archives":  {"size": 0, "count": 0, "color": "#f59e0b"},
        "other":     {"size": 0, "count": 0, "color": "#94a3b8"},
    }

    for mimetype, size in files:
        mt = (mimetype or "").lower()
        size = size or 0

        if any(x in mt for x in ["pdf", "word", "excel", "spreadsheet",
                                   "presentation", "document", "text"]):
            cat = "documents"
        elif any(x in mt for x in ["image", "video", "audio"]):
            cat = "media"
        elif any(x in mt for x in ["zip", "rar", "7z", "tar", "gzip",
                                     "compressed", "archive"]):
            cat = "archives"
        else:
            cat = "other"

        categories[cat]["size"] += size
        categories[cat]["count"] += 1

    total = sum(c["size"] for c in categories.values())

    return {
        "total_bytes": total,
        "total_mb": round(total / (1024 * 1024), 2),
        "categories": [
            {
                "name": name.capitalize(),
                "size_bytes": cat["size"],
                "size_mb": round(cat["size"] / (1024 * 1024), 2),
                "count": cat["count"],
                "pct": round((cat["size"] / total * 100), 1) if total > 0 else 0,
                "color": cat["color"],
            }
            for name, cat in categories.items()
        ],
    }