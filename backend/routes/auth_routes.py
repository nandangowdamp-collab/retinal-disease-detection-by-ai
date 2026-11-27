from flask import Blueprint, current_app, g, jsonify, request
from models.doctor_model import DoctorModel
from models.patient_model import PatientModel
from models.user_model import UserModel
from services.auth_service import (
    AuthError,
    change_user_password,
    login_user,
    logout_user,
    register_user,
)
from utils.decorators import record_audit_log, require_db, require_roles
from utils.validators import sanitize_text, validate_phone, validate_positive_int

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def _limiter():
    return current_app.extensions.get("limiter")


@auth_bp.post("/register")
@require_db
def register():
    limiter = _limiter()
    if limiter:
        limiter.check()
    data = request.get_json(silent=True) or {}
    try:
        result = register_user(data)
        return jsonify(result), 201
    except AuthError as exc:
        return jsonify({"error": exc.message}), exc.status_code


@auth_bp.post("/login")
@require_db
def login():
    data = request.get_json(silent=True) or {}
    expected_role = sanitize_text(data.get("expected_role"), 20).lower() or None
    try:
        result = login_user(data, expected_role=expected_role)
        return jsonify(result), 200
    except AuthError as exc:
        return jsonify({"error": exc.message}), exc.status_code


@auth_bp.post("/logout")
@require_roles("patient", "doctor", "admin")
def logout():
    logout_user(g.current_claims, g.current_user_id)
    return jsonify({"message": "Logged out successfully."}), 200


@auth_bp.get("/profile")
@require_roles("patient", "doctor", "admin")
def get_profile():
    user = g.current_user
    role = user.get("role")
    profile = None
    if role == "patient":
        profile = PatientModel.to_public(PatientModel.find_by_user_id(g.current_user_id))
    elif role == "doctor":
        profile = DoctorModel.to_public(DoctorModel.find_by_user_id(g.current_user_id))
    return jsonify({"user": UserModel.to_public(user), "profile": profile}), 200


@auth_bp.put("/profile")
@require_roles("patient", "doctor", "admin")
def update_profile():
    data = request.get_json(silent=True) or {}
    user_updates: dict = {}

    if "full_name" in data:
        name = sanitize_text(data.get("full_name"), 120)
        if not name:
            return jsonify({"error": "Full name cannot be empty."}), 400
        user_updates["full_name"] = name

    if "phone" in data:
        phone = sanitize_text(data.get("phone"), 30)
        if not validate_phone(phone):
            return jsonify({"error": "Invalid phone number."}), 400
        user_updates["phone"] = phone

    updated_user = (
        UserModel.update_by_id(g.current_user_id, user_updates) if user_updates else g.current_user
    )

    role = g.current_user.get("role")
    profile = None
    if role == "patient":
        p_updates: dict = {}
        if "age" in data:
            age = validate_positive_int(data.get("age"), 1, 120)
            if age is None:
                return jsonify({"error": "Age must be between 1 and 120."}), 400
            p_updates["age"] = age
        if "gender" in data:
            p_updates["gender"] = sanitize_text(data.get("gender"), 30)
        if "address" in data:
            p_updates["address"] = sanitize_text(data.get("address"), 300)
        profile_doc = (
            PatientModel.update_by_user_id(g.current_user_id, p_updates)
            if p_updates
            else PatientModel.find_by_user_id(g.current_user_id)
        )
        profile = PatientModel.to_public(profile_doc)
    elif role == "doctor":
        d_updates: dict = {}
        for field in ("qualification", "specialization", "hospital_name", "availability"):
            if field in data:
                d_updates[field] = sanitize_text(data.get(field), 160)
        if "experience" in data:
            exp = validate_positive_int(data.get("experience"), 0, 80)
            if exp is None:
                return jsonify({"error": "Experience must be between 0 and 80 years."}), 400
            d_updates["experience"] = exp
        profile_doc = (
            DoctorModel.update_by_user_id(g.current_user_id, d_updates)
            if d_updates
            else DoctorModel.find_by_user_id(g.current_user_id)
        )
        profile = DoctorModel.to_public(profile_doc)

    record_audit_log(g.current_user_id, "PROFILE_UPDATED", "user", g.current_user_id)
    return jsonify({"user": UserModel.to_public(updated_user), "profile": profile}), 200


@auth_bp.put("/change-password")
@require_roles("patient", "doctor", "admin")
def change_password():
    data = request.get_json(silent=True) or {}
    try:
        change_user_password(
            g.current_user,
            data.get("current_password", ""),
            data.get("new_password", ""),
            data.get("confirm_password", ""),
        )
        return jsonify({"message": "Password updated successfully."}), 200
    except AuthError as exc:
        return jsonify({"error": exc.message}), exc.status_code
