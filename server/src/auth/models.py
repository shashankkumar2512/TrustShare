from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    organization: Optional[str] = None


class RefreshRequest(BaseModel):
    refresh_token: str


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: str
    plan: str
    is_active: bool
    mfa_enabled: bool
    storage_used: Optional[int] = 0
    storage_quota: Optional[int] = 5368709120
    avatar_color: Optional[str] = "linear-gradient(135deg,#3b82f6,#8b5cf6)"
    organization: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    user: Optional[UserOut] = None
    mfa_required: bool = False
    mfa_token: Optional[str] = None


class MeResponse(BaseModel):
    user: UserOut


class VerifyOTPRequest(BaseModel):
    mfa_token: str
    code: str


class ResendOTPRequest(BaseModel):
    mfa_token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class VerifyMFASetupRequest(BaseModel):
    code: str


class DisableMFARequest(BaseModel):
    password: str


class OAuthExchangeRequest(BaseModel):
    code: str