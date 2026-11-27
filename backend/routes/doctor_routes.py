from datetime import datetime, timezone
from bson import ObjectId
from flask import Blueprint, g, jsonify, request

from database.db import get_db
from models.doctor_model import DoctorModel
from models.patient_model import PatientModel
from models.prediction_model import PredictionModel
from models.user_model import UserModel
from services.consultation_service import (
    ConsultationError,
    get_authorized_consultations,
    update_consultation_by_doctor,
)
from services.prediction_service import query_predictions
from utils.decorators import record_audit_log, require_roles, require_verified_doctor
from utils.validators import sanitize_text, validate_phone, validate_positive_int

doctor_bp = Blueprint("doctor", __name__, url_prefix="/api/doctor")


def _assigned_patient_ids(doctor_user_id: str) -> list[str]:
    db = get_db()
    consultations = db.consultations.find({"doctor_id": doctor_user_id}, {"patient_id": 1})
    return list({c["patient_id"] for c in consultations if c.get("patient_id")})


@doctor_bp.get("/dashboard")
@require_roles("doctor")
def doctor_dashboard():
    db = get_db()
    did = g.current_user_id
    doc_profile = DoctorModel.find_by_user_id(did)
    verification_status = doc_profile.get("verification_status", "pending") if doc_profile else "pending"

    if verification_status != "verified":
        return (
            jsonify(
                {
                    "user": UserModel.to_public(g.current_user),
                    "profile": DoctorModel.to_public(doc_profile),
                    "verification_status": verification_status,
                    "stats": {
                        "assigned_patients": 0,
                        "total_consultations": 0,
                        "pending_consultations": 0,
                        "completed_consultations": 0,
                        "unread_messages": 0,
                    },
                    "recent_consultations": [],
                    "recent_activities": [],
                }
            ),
            200,
        )

    consultations = get_authorized_consultations(did, "doctor")
    assigned_ids = _assigned_patient_ids(did)
    pending = sum(1 for c in consultations if c.get("consultation_status") == "pending")
    completed = sum(1 for c in consultations if c.get("consultation_status") == "completed")
    unread = db.messages.count_documents({"receiver_id": did, "read_at": None})

    return (
        jsonify(
            {
                "user": UserModel.to_public(g.current_user),
                "profile": DoctorModel.to_public(doc_profile),
                "verification_status": verification_status,
                "stats": {
                    "assigned_patients": len(assigned_ids),
                    "total_consultations": len(consultations),
                    "pending_consultations": pending,
                    "completed_consultations": completed,
                    "unread_messages": unread,
                },
                "recent_consultations": consultations[:6],
                "recent_activities": consultations[:6],
            }
        ),
        200,
    )


@doctor_bp.get("/profile")
@require_roles("doctor")
def get_doctor_profile():
    doc_profile = DoctorModel.to_public(DoctorModel.find_by_user_id(g.current_user_id))
    return jsonify({"user": UserModel.to_public(g.current_user), "profile": doc_profile}), 200


@doctor_bp.put("/profile")
@require_roles("doctor")
def update_doctor_profile():
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

    d_updates: dict = {}
    for field in ("qualification", "specialization", "hospital_name", "availability"):
        if field in data:
            d_updates[field] = sanitize_text(data.get(field), 160)
    if "experience" in data:
        exp = validate_positive_int(data.get("experience"), 0, 80)
        if exp is None:
            return jsonify({"error": "Experience must be between 0 and 80."}), 400
        d_updates["experience"] = exp

    profile = (
        DoctorModel.update_by_user_id(g.current_user_id, d_updates)
        if d_updates
        else DoctorModel.find_by_user_id(g.current_user_id)
    )
    return (
        jsonify({"user": UserModel.to_public(updated_user), "profile": DoctorModel.to_public(profile)}),
        200,
    )


@doctor_bp.get("/patients")
@require_verified_doctor
def get_assigned_patients():
    db = get_db()
    did = g.current_user_id
    patient_ids = _assigned_patient_ids(did)
    if not patient_ids:
        return jsonify({"patients": []}), 200

    oids = [ObjectId(pid) for pid in patient_ids if ObjectId.is_valid(pid)]
    users = list(db.users.find({"_id": {"$in": oids}}))
    profiles = {p["user_id"]: p for p in db.patients.find({"user_id": {"$in": patient_ids}})}

    patients = []
    for u in users:
        uid = str(u["_id"])
        prof = profiles.get(uid, {})
        pred_count = db.predictions.count_documents({"patient_id": uid})
        consult_count = db.consultations.count_documents({"patient_id": uid, "doctor_id": did})
        latest_pred = db.predictions.find_one({"patient_id": uid}, sort=[("prediction_date", -1)])
        patients.append(
            {
                "id": uid,
                "full_name": u.get("full_name"),
                "email": u.get("email"),
                "phone": u.get("phone"),
                "age": prof.get("age"),
                "gender": prof.get("gender"),
                "address": prof.get("address"),
                "prediction_count": pred_count,
                "consultation_count": consult_count,
                "latest_prediction": PredictionModel.to_public(latest_pred) if latest_pred else None,
            }
        )
    return jsonify({"patients": patients}), 200


@doctor_bp.get("/patients/<patient_id>")
@require_verified_doctor
def get_patient_details(patient_id: str):
    db = get_db()
    did = g.current_user_id
    authorized = db.consultations.find_one({"doctor_id": did, "patient_id": patient_id})
    if not authorized:
        return jsonify({"error": "You are only authorized to access patients assigned to you."}), 403

    user = UserModel.find_by_id(patient_id)
    if not user:
        return jsonify({"error": "Patient not found."}), 404

    profile = PatientModel.to_public(PatientModel.find_by_user_id(patient_id))
    predictions = query_predictions(patient_id=patient_id)
    consultations = [
        c for c in get_authorized_consultations(did, "doctor") if c.get("patient_id") == patient_id
    ]

    return (
        jsonify(
            {
                "patient": UserModel.to_public(user),
                "profile": profile,
                "predictions": predictions,
                "consultations": consultations,
            }
        ),
        200,
    )


@doctor_bp.get("/consultations")
@require_verified_doctor
def get_doctor_consultations():
    status = request.args.get("status", "")
    consultations = get_authorized_consultations(g.current_user_id, "doctor", status_filter=status)
    return jsonify({"consultations": consultations}), 200


@doctor_bp.put("/consultations/<consultation_id>")
@require_verified_doctor
def update_consultation(consultation_id: str):
    data = request.get_json(silent=True) or {}
    try:
        updated = update_consultation_by_doctor(consultation_id, g.current_user_id, data)
        return jsonify({"consultation": updated}), 200
    except ConsultationError as exc:
        return jsonify({"error": exc.message}), exc.status_code


@doctor_bp.post("/consultations/<consultation_id>/notes")
@require_verified_doctor
def add_consultation_notes(consultation_id: str):
    data = request.get_json(silent=True) or {}
    payload = {}
    if "consultation_notes" in data or "notes" in data:
        payload["consultation_notes"] = data.get("consultation_notes") or data.get("notes", "")
    if "recommendations" in data:
        payload["recommendations"] = data.get("recommendations", "")
    if "consultation_status" in data:
        payload["consultation_status"] = data.get("consultation_status")
    try:
        updated = update_consultation_by_doctor(consultation_id, g.current_user_id, payload)
        return jsonify({"consultation": updated}), 200
    except ConsultationError as exc:
        return jsonify({"error": exc.message}), exc.status_code


@doctor_bp.put("/predictions/<prediction_id>/assessment")
@require_verified_doctor
def add_prediction_assessment(prediction_id: str):
    db = get_db()
    pred = PredictionModel.find_by_id(prediction_id)
    if not pred:
        return jsonify({"error": "Prediction record not found."}), 404

    authorized = db.consultations.find_one(
        {"doctor_id": g.current_user_id, "patient_id": pred.get("patient_id")}
    )
    if not authorized:
        return jsonify({"error": "You are not authorized to assess predictions for this patient."}), 403

    data = request.get_json(silent=True) or {}
    impression = sanitize_text(data.get("clinical_impression"), 200)
    notes = sanitize_text(data.get("assessment_notes"), 2000)
    if not impression and not notes:
        return jsonify({"error": "Provide clinical_impression or assessment_notes."}), 400

    assessment = {
        "doctor_id": g.current_user_id,
        "doctor_name": g.current_user.get("full_name"),
        "clinical_impression": impression,
        "assessment_notes": notes,
        "updated_at": datetime.now(timezone.utc),
    }
    db.predictions.update_one({"_id": pred["_id"]}, {"$set": {"doctor_assessment": assessment}})
    record_audit_log(g.current_user_id, "DOCTOR_ASSESSMENT_ADDED", "prediction", str(pred["_id"]))
    updated = PredictionModel.find_by_id(str(pred["_id"]))
    return jsonify({"prediction": PredictionModel.to_public(updated)}), 200
