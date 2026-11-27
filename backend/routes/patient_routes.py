from flask import Blueprint, g, jsonify, request
from database.db import get_db
from models.doctor_model import DoctorModel
from models.patient_model import PatientModel
from models.user_model import UserModel
from services.consultation_service import get_authorized_consultations
from services.prediction_service import query_predictions
from utils.decorators import require_roles
from utils.validators import sanitize_text, validate_phone, validate_positive_int

patient_bp = Blueprint("patient", __name__, url_prefix="/api/patient")


@patient_bp.get("/dashboard")
@require_roles("patient")
def patient_dashboard():
    db = get_db()
    pid = g.current_user_id
    patient_profile = PatientModel.to_public(PatientModel.find_by_user_id(pid))
    total_predictions = db.predictions.count_documents({"patient_id": pid})
    recent_predictions = query_predictions(patient_id=pid, limit=5)
    consultations = get_authorized_consultations(pid, "patient")
    unread_messages = db.messages.count_documents({"receiver_id": pid, "read_at": None})

    return (
        jsonify(
            {
                "user": UserModel.to_public(g.current_user),
                "profile": patient_profile,
                "stats": {
                    "total_images": total_predictions,
                    "total_predictions": total_predictions,
                    "total_consultations": len(consultations),
                    "unread_messages": unread_messages,
                },
                "recent_predictions": recent_predictions,
                "recent_consultations": consultations[:5],
            }
        ),
        200,
    )


@patient_bp.get("/profile")
@require_roles("patient")
def get_patient_profile():
    profile = PatientModel.to_public(PatientModel.find_by_user_id(g.current_user_id))
    consultations = get_authorized_consultations(g.current_user_id, "patient")
    return (
        jsonify(
            {
                "user": UserModel.to_public(g.current_user),
                "profile": profile,
                "consultations": consultations,
            }
        ),
        200,
    )


@patient_bp.put("/profile")
@require_roles("patient")
def update_patient_profile():
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

    profile = (
        PatientModel.update_by_user_id(g.current_user_id, p_updates)
        if p_updates
        else PatientModel.find_by_user_id(g.current_user_id)
    )
    return (
        jsonify({"user": UserModel.to_public(updated_user), "profile": PatientModel.to_public(profile)}),
        200,
    )


@patient_bp.get("/predictions")
@require_roles("patient")
def get_patient_predictions():
    search = request.args.get("search", "")
    disease = request.args.get("disease", "")
    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")
    records = query_predictions(
        patient_id=g.current_user_id,
        search=search,
        disease=disease,
        start_date=start_date,
        end_date=end_date,
    )
    return jsonify({"predictions": records}), 200


@patient_bp.get("/doctors")
@require_roles("patient")
def list_available_doctors():
    db = get_db()
    search = sanitize_text(request.args.get("search", ""), 100).lower()
    verified_docs = list(db.doctors.find({"verification_status": "verified"}))

    results = []
    for doc in verified_docs:
        user = UserModel.find_by_id(doc["user_id"])
        if not user or user.get("account_status") != "active":
            continue
        combined = {
            "id": str(user["_id"]),
            "full_name": user.get("full_name"),
            "email": user.get("email"),
            "phone": user.get("phone"),
            **DoctorModel.to_public(doc),
            "doctor_profile_id": str(doc["_id"]),
        }
        combined["id"] = str(user["_id"])
        if search:
            haystack = f"{combined['full_name']} {combined['specialization']} {combined['hospital_name']}".lower()
            if search not in haystack:
                continue
        results.append(combined)

    return jsonify({"doctors": results}), 200
