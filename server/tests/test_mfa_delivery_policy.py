import pytest
from pydantic import ValidationError

from src.auth import service as auth_service
from src.auth.models import SignupRequest


@pytest.fixture(autouse=True)
def clear_otp_store():
    auth_service.otp_store.clear()
    yield
    auth_service.otp_store.clear()


def test_development_dummy_email_logs_otp_and_skips_smtp(monkeypatch, capsys):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("DEV_DUMMY_EMAIL_DOMAINS", "example.com,test.com")
    monkeypatch.setattr(auth_service.random, "randint", lambda *_: 483921)
    send_calls = []
    monkeypatch.setattr(
        auth_service.email_service,
        "send_otp_email",
        lambda *args: send_calls.append(args),
    )

    code = auth_service.generate_otp(27, "test@example.com", "Test User")

    output = capsys.readouterr().out
    assert code == "483921"
    assert auth_service.otp_store[27]["otp"] == code
    assert "[OTP DEV] User 27 -> 483921" in output
    assert "configured dummy/test domain: example.com" in output
    assert send_calls == []


def test_development_normal_email_logs_and_attempts_smtp(monkeypatch, capsys):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("DEV_DUMMY_EMAIL_DOMAINS", "example.com,test.com")
    monkeypatch.setenv("SMTP_USER", "sender@gmail.com")
    monkeypatch.setenv("SMTP_PASSWORD", "configured-app-password")
    monkeypatch.setattr(auth_service.random, "randint", lambda *_: 654321)
    send_calls = []
    monkeypatch.setattr(
        auth_service.email_service,
        "send_otp_email",
        lambda *args: send_calls.append(args),
    )

    code = auth_service.generate_otp(31, "user@gmail.com", "Normal User")

    output = capsys.readouterr().out
    assert auth_service.otp_store[31]["otp"] == code
    assert "[OTP DEV] User 31 -> 654321" in output
    assert send_calls == [("user@gmail.com", code, "Normal User")]


def test_development_email_failure_keeps_otp_usable(monkeypatch, capsys):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("DEV_DUMMY_EMAIL_DOMAINS", "example.com")
    monkeypatch.setattr(auth_service.random, "randint", lambda *_: 112233)

    def fail_delivery(*_args):
        raise ConnectionError("simulated SMTP outage")

    monkeypatch.setattr(auth_service.email_service, "send_otp_email", fail_delivery)

    code = auth_service.generate_otp(44, "user@gmail.com", "Offline User")

    output = capsys.readouterr().out
    assert code == "112233"
    assert auth_service.otp_store[44]["otp"] == code
    assert auth_service.verify_otp_code(44, code) is True
    assert "[OTP DEV] User 44 -> 112233" in output
    assert "[EMAIL ERROR] Failed to send MFA email: ConnectionError" in output


def test_production_never_logs_otp_value(monkeypatch, capsys):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("DEV_DUMMY_EMAIL_DOMAINS", "example.com")
    monkeypatch.setattr(auth_service.random, "randint", lambda *_: 778899)
    send_calls = []
    monkeypatch.setattr(
        auth_service.email_service,
        "send_otp_email",
        lambda *args: send_calls.append(args),
    )

    code = auth_service.generate_otp(52, "user@gmail.com", "Production User")

    monkeypatch.setattr(auth_service.email_service, "SMTP_USER", "")
    monkeypatch.setattr(auth_service.email_service, "SMTP_PASSWORD", "")
    auth_service.email_service._send_email(
        "user@gmail.com",
        "Your TrustShare Verification Code",
        f"Production OTP: {code}",
    )

    output = capsys.readouterr().out
    assert code == "778899"
    assert auth_service.otp_store[52]["otp"] == code
    assert code not in output
    assert "[OTP DEV]" not in output
    assert send_calls == [("user@gmail.com", code, "Production User")]


def test_signup_keeps_format_only_email_validation():
    example_user = SignupRequest(
        name="Example User",
        email="test@example.com",
        password="StrongPassword123!",
    )
    normal_user = SignupRequest(
        name="Normal User",
        email="something@gmail.com",
        password="StrongPassword123!",
    )

    assert str(example_user.email) == "test@example.com"
    assert str(normal_user.email) == "something@gmail.com"

    with pytest.raises(ValidationError):
        SignupRequest(
            name="Invalid Format",
            email="not-an-email",
            password="StrongPassword123!",
        )
