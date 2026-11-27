from flask import Blueprint, g, jsonify, request
from database.db import get_db
from models.consultation_model import ConsultationModel
from services.consultation_service import (
    ConsultationError,
    _enrich_consultations,
    create_consultation,
    get_authorized_consultations,
    update_consultation_by_doctor,
)
from utils.decorators import require_roles, require_verified_doctor

consultation_bp = Blueprint("consultations", __name__, url_prefix="/api/consultations")


@consultation_bp.post("")
@require_roles("patient")
def request_consultation():
    data = request.get_json(silent=True) or {}
    try:
        consultation = create_consultation(g.current_user_id, data)
        return jsonify({"consultation": consultation}), 201
    except ConsultationError as exc:
        return jsonify({"error": exc.message}), exc.status_code


@consultation_bp.get("")
@require_roles("patient", "doctor", "admin")
def list_consultations():
    role = g.current_user.get("role")
    if role == "doctor":
        doc = get_db().doctors.find_one({"user_id": g.current_user_id})
        if not doc or doc.get("verification_status") != "verified":
            return jsonify({"error": "Doctor verification required."}), 403

    status = request.args.get("status", "")
    try:
        consultations = get_authorized_consultations(g.current_user_id, role, status_filter=status)
        return jsonify({"consultations": consultations}), 200
    except ConsultationError as exc:
        return jsonify({"error": exc.message}), exc.status_code


@consultation_bp.get("/<consultation_id>")
@require_roles("patient", "doctor", "admin")
def get_consultation(consultation_id: str):
    doc = ConsultationModel.find_by_id(consultation_id)
    if not doc:
        return jsonify({"error": "Consultation not found."}), 404
    role = g.current_user.get("role")
    uid = g.current_user_id
    if role == "patient" and doc.get("patient_id") != uid:
        return jsonify({"error": "Unauthorized."}), 403
    if role == "doctor":
        prof = get_db().doctors.find_one({"user_id": uid, "verification_status": "verified"})
        if not prof or doc.get("doctor_id") != uid:
            return jsonify({"error": "Unauthorized."}), 403

    return jsonify({"consultation": _enrich_consultations([doc])[0]}), 200


@consultation_bp.put("/<consultation_id>/status")
@require_verified_doctor
def update_status(consultation_id: str):
    data = request.get_json(silent=True) or {}
    try:
        updated = update_consultation_by_doctor(consultation_id, g.current_user_id, data)
        return jsonify({"consultation": updated}), 200
    except ConsultationError as exc:
        return jsonify({"error": exc.message}), exc.status_code
