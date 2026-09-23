from src.auth.dependencies import create_access_token
from src.entities.audit_log import AuditLog
from src.entities.user import User


def _user(db, email: str, role: str = "member") -> User:
    user = User(
        name=email.split("@")[0],
        email=email,
        hashed_password="unused",
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _headers(user: User) -> dict[str, str]:
    token = create_access_token({"sub": str(user.id)})
    return {"Authorization": f"Bearer {token}"}


def test_activity_requires_authentication(client):
    response = client.get("/api/activity/")
    assert response.status_code == 401


def test_activity_returns_only_current_users_audit_events(client, db):
    owner = _user(db, "activity-owner@example.com")
    other = _user(db, "activity-other@example.com")
    db.add_all([
        AuditLog(user_id=owner.id, action="UPLOAD", resource_type="file", resource_name="owner.txt"),
        AuditLog(user_id=other.id, action="DOWNLOAD", resource_type="file", resource_name="private.txt"),
    ])
    db.commit()

    response = client.get("/api/activity/", headers=_headers(owner))

    assert response.status_code == 200
    assert [item["resource_name"] for item in response.json()] == ["owner.txt"]


def test_member_cannot_read_another_users_legacy_activity_route(client, db):
    owner = _user(db, "activity-route-owner@example.com")
    other = _user(db, "activity-route-other@example.com")

    response = client.get(f"/api/activity/user/{other.id}", headers=_headers(owner))

    assert response.status_code == 403


def test_admin_can_read_a_users_activity_route(client, db):
    owner = _user(db, "activity-admin-target@example.com")
    admin = _user(db, "activity-admin@example.com", role="admin")
    db.add(AuditLog(user_id=owner.id, action="SHARE", resource_type="file", resource_name="report.pdf"))
    db.commit()

    response = client.get(f"/api/activity/user/{owner.id}", headers=_headers(admin))

    assert response.status_code == 200
    assert response.json()[0]["action"] == "SHARE"


def test_clients_cannot_create_fake_activity(client, db):
    user = _user(db, "activity-no-fake@example.com")
    response = client.post(
        "/api/activity/",
        headers=_headers(user),
        json={"user_id": user.id, "action": "FAKE_EVENT"},
    )
    assert response.status_code == 405
