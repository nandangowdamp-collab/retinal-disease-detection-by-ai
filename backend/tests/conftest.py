import io
import sys
from pathlib import Path
import pytest
from PIL import Image

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from ai_model.predictor import set_predictor_override
from app import create_app
from database.db import reset_db_state
from models.user_model import UserModel


@pytest.fixture()
def app(tmp_path):
    reset_db_state()
    set_predictor_override(None)
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    application = create_app(
        {
            "TESTING": True,
            "MONGO_URI": "mongomock://localhost/retinal_test",
            "DATABASE_NAME": "retinal_test_db",
            "SECRET_KEY": "test-secret-key-for-pytest",
            "JWT_SECRET_KEY": "test-jwt-secret-key-for-pytest",
            "UPLOAD_FOLDER": str(upload_dir),
            "MODEL_PATH": str(tmp_path / "missing_model.keras"),
            "MODEL_CONFIG_PATH": str(tmp_path / "missing_preprocessing.json"),
        }
    )
    yield application
    set_predictor_override(None)
    reset_db_state()


@pytest.fixture()
def client(app):
    return app.test_client()


def make_png_bytes(width=128, height=128, color=(180, 70, 50)) -> io.BytesIO:
    buf = io.BytesIO()
    img = Image.new("RGB", (width, height), color=color)
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


def register_and_login_patient(client, email="patient1@example.com", name="Aarav Patient"):
    client.post(
        "/api/auth/register",
        json={
            "role": "patient",
            "full_name": name,
            "email": email,
            "phone": "+15551234567",
            "age": 38,
            "gender": "Male",
            "address": "123 Vision Ave",
            "password": "Password123",
            "confirm_password": "Password123",
        },
    )
    res = client.post(
        "/api/auth/login",
        json={"email": email, "password": "Password123", "expected_role": "patient"},
    )
    data = res.get_json()
    return data["access_token"], data["user"]["id"]


def register_and_login_doctor(
    client,
    email="doctor1@example.com",
    reg_num="MED-1001",
    name="Dr. Priya Nair",
):
    client.post(
        "/api/auth/register",
        json={
            "role": "doctor",
            "full_name": name,
            "email": email,
            "phone": "+15559876543",
            "registration_number": reg_num,
            "qualification": "MBBS, MS",
            "specialization": "Retina Specialist",
            "experience": 10,
            "hospital_name": "Eye Care Center",
            "password": "Password123",
            "confirm_password": "Password123",
        },
    )
    res = client.post(
        "/api/auth/login",
        json={"email": email, "password": "Password123", "expected_role": "doctor"},
    )
    data = res.get_json()
    return data["access_token"], data["user"]["id"]


def create_and_login_admin(app, client, email="admin@example.com"):
    with app.app_context():
        UserModel.create(
            full_name="System Admin",
            email=email,
            phone="+15550000000",
            password="AdminSuperPassword1234",
            role="admin",
        )
    res = client.post(
        "/api/auth/login",
        json={"email": email, "password": "AdminSuperPassword1234", "expected_role": "admin"},
    )
    data = res.get_json()
    return data["access_token"], data["user"]["id"]
