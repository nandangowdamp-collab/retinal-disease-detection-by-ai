from datetime import datetime, timezone
from flask_jwt_extended import create_access_token
from werkzeug.security import generate_password_hash

from database.db import get_db
from models.doctor_model import DoctorModel
from models.patient_model import PatientModel
from models.user_model import UserModel
from utils.decorators import record_audit_log
from utils.validators import (
    sanitize_text,
    validate_email,
    validate_password,
    validate_phone,
    validate_positive_int,
    validate_required_fields,
)


class AuthError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def register_user(data: dict) -> dict:
    role = sanitize_text(data.get("role", "patient"), 20).lower()
    if role == "admin":
        raise AuthError("Administrator accounts cannot be created via public registration.", 403)
    if role not in ("patient", "doctor"):
        raise AuthError("Role must be either 'patient' or 'doctor'.", 400)

    common_required = ["full_name", "email", "phone", "password", "confirm_password"]
    missing = validate_required_fields(data, common_required)
    if missing:
        raise AuthError(f"Missing required fields: {', '.join(missing)}.", 400)

    email = sanitize_text(data.get("email"), 200).lower()
    if not validate_email(email):
        raise AuthError("Please enter a valid email address.", 400)

    phone = sanitize_text(data.get("phone"), 30)
    if not validate_phone(phone):
        raise AuthError("Please enter a valid phone number.", 400)

    password = data.get("password", "")
    confirm_password = data.get("confirm_password", "")
    if password != confirm_password:
        raise AuthError("Password and confirm password do not match.", 400)

    ok_pw, pw_err = validate_password(password, min_length=8)
    if not ok_pw:
        raise AuthError(pw_err, 400)

    if UserModel.find_by_email(email):
        raise AuthError("An account with this email address already exists.", 409)

    full_name = sanitize_text(data.get("full_name"), 120)

    if role == "patient":
        missing_patient = validate_required_fields(data, ["age", "gender", "address"])
        if missing_patient:
            raise AuthError(f"Missing required patient fields: {', '.join(missing_patient)}.", 400)
        age = validate_positive_int(data.get("age"), min_val=1, max_val=120)
        if age is None:
            raise AuthError("Age must be a valid number between 1 and 120.", 400)
        gender = sanitize_text(data.get("gender"), 30)
        address = sanitize_text(data.get("address"), 300)

        user_doc = UserModel.create(full_name, email, phone, password, role="patient")
        patient_doc = PatientModel.create(str(user_doc["_id"]), age, gender, address)
        record_audit_log(str(user_doc["_id"]), "PATIENT_REGISTERED", "user", str(user_doc["_id"]))
        return {
            "message": "Patient registration successful. Please log in.",
            "user": UserModel.to_public(user_doc),
            "profile": PatientModel.to_public(patient_doc),
        }

    # Doctor registration
    doc_required = [
        "registration_number",
        "qualification",
        "specialization",
        "experience",
        "hospital_name",
    ]
    missing_doc = validate_required_fields(data, doc_required)
    if missing_doc:
        raise AuthError(f"Missing required doctor fields: {', '.join(missing_doc)}.", 400)

    reg_num = sanitize_text(data.get("registration_number"), 80)
    if DoctorModel.find_by_registration_number(reg_num):
        raise AuthError("A doctor with this medical registration number already exists.", 409)

    experience = validate_positive_int(data.get("experience"), min_val=0, max_val=80)
    if experience is None:
        raise AuthError("Years of experience must be a valid number between 0 and 80.", 400)

    user_doc = UserModel.create(full_name, email, phone, password, role="doctor")
    doctor_doc = DoctorModel.create(
        user_id=str(user_doc["_id"]),
        qualification=sanitize_text(data.get("qualification"), 120),
        specialization=sanitize_text(data.get("specialization"), 120),
        registration_number=reg_num,
        experience=experience,
        hospital_name=sanitize_text(data.get("hospital_name"), 160),
        verification_status="pending",
        availability=sanitize_text(data.get("availability"), 120) or "Mon - Fri, 09:00 AM - 05:00 PM",
    )
    record_audit_log(str(user_doc["_id"]), "DOCTOR_REGISTERED", "doctor", str(doctor_doc["_id"]))
    return {
        "message": "Doctor registration submitted. Your account awaits administrator verification.",
        "user": UserModel.to_public(user_doc),
        "profile": DoctorModel.to_public(doctor_doc),
    }


def login_user(data: dict, expected_role: str | None = None) -> dict:
    email = sanitize_text(data.get("email"), 200).lower()
    password = data.get("password", "")
    if not email or not password:
        raise AuthError("Email and password are required.", 400)

    user_doc = UserModel.find_by_email(email)
    if not user_doc or not UserModel.verify_password(user_doc, password):
        raise AuthError("Invalid email or password.", 401)

    if user_doc.get("account_status") != "active":
        raise AuthError("This account has been deactivated. Contact an administrator.", 403)

    role = user_doc.get("role")
    if expected_role and role != expected_role:
        raise AuthError(f"Access denied. Please sign in through the {role} portal.", 403)

    user_id = str(user_doc["_id"])
    profile = None
    if role == "patient":
        profile = PatientModel.to_public(PatientModel.find_by_user_id(user_id))
    elif role == "doctor":
        profile = DoctorModel.to_public(DoctorModel.find_by_user_id(user_id))

    token = create_access_token(
        identity=user_id,
        additional_claims={"role": role, "email": user_doc["email"]},
    )
    record_audit_log(user_id, "USER_LOGIN", "user", user_id, {"role": role})
    return {
        "access_token": token,
        "user": UserModel.to_public(user_doc),
        "profile": profile,
    }


def logout_user(claims: dict, user_id: str) -> None:
    jti = claims.get("jti")
    if jti:
        get_db().revoked_tokens.update_one(
            {"jti": jti},
            {"$set": {"jti": jti, "user_id": user_id, "revoked_at": datetime.now(timezone.utc)}},
            upsert=True,
        )
    record_audit_log(user_id, "USER_LOGOUT", "user", user_id)


def change_user_password(user_doc: dict, current_password: str, new_password: str, confirm_password: str) -> None:
    if not current_password or not UserModel.verify_password(user_doc, current_password):
        raise AuthError("Current password is incorrect.", 400)
    if new_password != confirm_password:
        raise AuthError("New password and confirmation do not match.", 400)
    min_len = 16 if user_doc.get("role") == "admin" else 8
    ok_pw, pw_err = validate_password(new_password, min_length=min_len)
    if not ok_pw:
        raise AuthError(pw_err, 400)

    UserModel.update_by_id(str(user_doc["_id"]), {"password_hash": generate_password_hash(new_password)})
    record_audit_log(str(user_doc["_id"]), "PASSWORD_CHANGED", "user", str(user_doc["_id"]))
