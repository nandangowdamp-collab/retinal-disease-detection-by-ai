from app import create_app
from database.db import reset_db_state


def test_patient_registration_and_login(client):
    res = client.post(
        "/api/auth/register",
        json={
            "role": "patient",
            "full_name": "Neha Kapoor",
            "email": "neha@example.com",
            "phone": "+15551112222",
            "age": 45,
            "gender": "Female",
            "address": "42 Oak Street",
            "password": "Password123",
            "confirm_password": "Password123",
        },
    )
    assert res.status_code == 201
    assert res.get_json()["user"]["role"] == "patient"

    dup = client.post(
        "/api/auth/register",
        json={
            "role": "patient",
            "full_name": "Neha Duplicate",
            "email": "neha@example.com",
            "phone": "+15551112222",
            "age": 45,
            "gender": "Female",
            "address": "42 Oak Street",
            "password": "Password123",
            "confirm_password": "Password123",
        },
    )
    assert dup.status_code == 409

    login_res = client.post(
        "/api/auth/login",
        json={"email": "neha@example.com", "password": "Password123", "expected_role": "patient"},
    )
    assert login_res.status_code == 200
    token = login_res.get_json()["access_token"]

    wrong_portal = client.post(
        "/api/auth/login",
        json={"email": "neha@example.com", "password": "Password123", "expected_role": "doctor"},
    )
    assert wrong_portal.status_code == 403

    # Logout revokes token
    out = client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert out.status_code == 200
    after = client.get("/api/auth/profile", headers={"Authorization": f"Bearer {token}"})
    assert after.status_code == 401


def test_public_admin_registration_blocked(client):
    res = client.post(
        "/api/auth/register",
        json={
            "role": "admin",
            "full_name": "Attacker",
            "email": "attacker@example.com",
            "phone": "+15551112222",
            "password": "Password123",
            "confirm_password": "Password123",
        },
    )
    assert res.status_code == 403


def test_missing_mongo_uri_returns_503(tmp_path):
    reset_db_state()
    degraded_app = create_app(
        {
            "TESTING": True,
            "MONGO_URI": "",
            "UPLOAD_FOLDER": str(tmp_path / "uploads"),
        }
    )
    c = degraded_app.test_client()
    health = c.get("/api/health").get_json()
    assert health["database"] == "unavailable"
    reg = c.post("/api/auth/register", json={"email": "a@b.com"})
    assert reg.status_code == 503
    reset_db_state()
