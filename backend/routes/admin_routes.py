from bson import ObjectId
from flask import Blueprint, current_app, g, jsonify, request

from ai_model.predictor import get_predictor
from database.db import get_db, parse_object_id, serialize_doc
from models.doctor_model import DoctorModel
from models.patient_model import PatientModel
from models.user_model import UserModel
from services.consultation_service import get_authorized_consultations
from services.prediction_service import query_predictions
from utils.decorators import record_audit_log, require_roles
from utils.validators import sanitize_text, validate_phone, validate_positive_int

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


@admin_bp.get("/dashboard")
@require_roles("admin")
def admin_dashboard():
    db = get_db()
    total_patients = db.users.count_documents({"role": "patient"})
    total_doctors = db.users.count_documents({"role": "doctor"})
    verified_doctors = db.doctors.count_documents({"verification_status": "verified"})
    pending_doctors = db.doctors.count_documents({"verification_status": "pending"})
    total_predictions = db.predictions.count_documents({})
    total_consultations = db.consultations.count_documents({})
    total_conversations = db.conversations.count_documents({})
    total_messages = db.messages.count_documents({})

    disease_counts = {}
    for cls in ("Normal", "Glaucoma", "Hypertensive Retinopathy", "Diabetic Retinopathy"):
        disease_counts[cls] = db.predictions.count_documents({"predicted_class": cls})

    consult_status_counts = {}
    for st in ("pending", "accepted", "rejected", "completed"):
        consult_status_counts[st] = db.consultations.count_documents({"consultation_status": st})

    predictor = get_predictor(current_app.config["MODEL_PATH"], current_app.config["MODEL_CONFIG_PATH"])
    model_ready, model_msg = predictor.is_ready()

    return (
        jsonify(
            {
                "stats": {
                    "total_patients": total_patients,
                    "total_doctors": total_doctors,
                    "verified_doctors": verified_doctors,
                    "pending_doctor_approvals": pending_doctors,
                    "total_images_uploaded": total_predictions,
                    "total_predictions": total_predictions,
                    "total_consultations": total_consultations,
                    "total_active_conversations": total_conversations,
                    "total_messages": total_messages,
                },
                "charts": {
                    "disease_distribution": disease_counts,
                    "consultation_status": consult_status_counts,
                },
                "model_status": {
                    "ready": model_ready,
                    "message": model_msg or "Model and preprocessing configuration verified.",
                },
            }
        ),
        200,
    )


@admin_bp.get("/patients")
@require_roles("admin")
def admin_list_patients():
    db = get_db()
    search = sanitize_text(request.args.get("search", ""), 100).lower()
    users = list(db.users.find({"role": "patient"}).sort("created_at", -1))
    profiles = {p["user_id"]: p for p in db.patients.find({})}

    patients = []
    for u in users:
        uid = str(u["_id"])
        prof = profiles.get(uid, {})
        if search:
            hay = f"{u.get('full_name', '')} {u.get('email', '')} {u.get('phone', '')}".lower()
            if search not in hay:
                continue
        patients.append(
            {
                **UserModel.to_public(u),
                "age": prof.get("age"),
                "gender": prof.get("gender"),
                "address": prof.get("address"),
                "prediction_count": db.predictions.count_documents({"patient_id": uid}),
                "consultation_count": db.consultations.count_documents({"patient_id": uid}),
            }
        )
    return jsonify({"patients": patients}), 200


@admin_bp.get("/patients/<patient_id>")
@require_roles("admin")
def admin_get_patient(patient_id: str):
    user = UserModel.find_by_id(patient_id)
    if not user or user.get("role") != "patient":
        return jsonify({"error": "Patient not found."}), 404
    profile = PatientModel.to_public(PatientModel.find_by_user_id(patient_id))
    predictions = query_predictions(patient_id=patient_id)
    consultations = [
        c for c in get_authorized_consultations(g.current_user_id, "admin") if c.get("patient_id") == patient_id
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


@admin_bp.put("/patients/<patient_id>")
@require_roles("admin")
def admin_update_patient(patient_id: str):
    user = UserModel.find_by_id(patient_id)
    if not user or user.get("role") != "patient":
        return jsonify({"error": "Patient not found."}), 404
    data = request.get_json(silent=True) or {}

    u_updates: dict = {}
    if "full_name" in data:
        u_updates["full_name"] = sanitize_text(data["full_name"], 120)
    if "phone" in data:
        if not validate_phone(data["phone"]):
            return jsonify({"error": "Invalid phone number."}), 400
        u_updates["phone"] = sanitize_text(data["phone"], 30)
    if "account_status" in data and data["account_status"] in ("active", "inactive"):
        u_updates["account_status"] = data["account_status"]

    if u_updates:
        user = UserModel.update_by_id(patient_id, u_updates)

    p_updates: dict = {}
    if "age" in data:
        age = validate_positive_int(data["age"], 1, 120)
        if age is None:
            return jsonify({"error": "Invalid age."}), 400
        p_updates["age"] = age
    if "gender" in data:
        p_updates["gender"] = sanitize_text(data["gender"], 30)
    if "address" in data:
        p_updates["address"] = sanitize_text(data["address"], 300)

    profile = (
        PatientModel.update_by_user_id(patient_id, p_updates)
        if p_updates
        else PatientModel.find_by_user_id(patient_id)
    )
    record_audit_log(g.current_user_id, "ADMIN_UPDATED_PATIENT", "patient", patient_id)
    return jsonify({"patient": UserModel.to_public(user), "profile": PatientModel.to_public(profile)}), 200


@admin_bp.get("/doctors")
@require_roles("admin")
def admin_list_doctors():
    db = get_db()
    status_filter = sanitize_text(request.args.get("verification_status", ""), 30).lower()
    users = list(db.users.find({"role": "doctor"}).sort("created_at", -1))
    doc_profiles = {d["user_id"]: d for d in db.doctors.find({})}

    doctors = []
    for u in users:
        uid = str(u["_id"])
        prof = doc_profiles.get(uid, {})
        v_status = prof.get("verification_status", "pending")
        if status_filter and status_filter != "all" and v_status != status_filter:
            continue
        doctors.append(
            {
                **UserModel.to_public(u),
                "doctor_profile_id": str(prof.get("_id", "")),
                "qualification": prof.get("qualification", ""),
                "specialization": prof.get("specialization", ""),
                "registration_number": prof.get("registration_number", ""),
                "experience": prof.get("experience", 0),
                "hospital_name": prof.get("hospital_name", ""),
                "verification_status": v_status,
                "rejection_reason": prof.get("rejection_reason", ""),
                "availability": prof.get("availability", ""),
                "consultation_count": db.consultations.count_documents({"doctor_id": uid}),
            }
        )
    return jsonify({"doctors": doctors}), 200


@admin_bp.put("/doctors/<doctor_id>")
@require_roles("admin")
def admin_update_doctor(doctor_id: str):
    user = UserModel.find_by_id(doctor_id)
    if not user or user.get("role") != "doctor":
        return jsonify({"error": "Doctor not found."}), 404
    data = request.get_json(silent=True) or {}

    u_updates: dict = {}
    if "full_name" in data:
        u_updates["full_name"] = sanitize_text(data["full_name"], 120)
    if "phone" in data and validate_phone(data["phone"]):
        u_updates["phone"] = sanitize_text(data["phone"], 30)
    if "account_status" in data and data["account_status"] in ("active", "inactive"):
        u_updates["account_status"] = data["account_status"]
    if u_updates:
        user = UserModel.update_by_id(doctor_id, u_updates)

    d_updates: dict = {}
    for field in ("qualification", "specialization", "hospital_name", "availability"):
        if field in data:
            d_updates[field] = sanitize_text(data[field], 160)
    if "experience" in data:
        exp = validate_positive_int(data["experience"], 0, 80)
        if exp is not None:
            d_updates["experience"] = exp

    prof = (
        DoctorModel.update_by_user_id(doctor_id, d_updates)
        if d_updates
        else DoctorModel.find_by_user_id(doctor_id)
    )
    record_audit_log(g.current_user_id, "ADMIN_UPDATED_DOCTOR", "doctor", doctor_id)
    return jsonify({"doctor": UserModel.to_public(user), "profile": DoctorModel.to_public(prof)}), 200


@admin_bp.put("/doctors/<doctor_id>/verify")
@require_roles("admin")
def admin_verify_doctor(doctor_id: str):
    user = UserModel.find_by_id(doctor_id)
    if not user or user.get("role") != "doctor":
        return jsonify({"error": "Doctor not found."}), 404

    data = request.get_json(silent=True) or {}
    status = sanitize_text(data.get("verification_status"), 20).lower()
    if status not in ("verified", "rejected", "pending"):
        return jsonify({"error": "verification_status must be 'verified', 'rejected', or 'pending'."}), 400

    updates = {
        "verification_status": status,
        "rejection_reason": sanitize_text(data.get("rejection_reason"), 500) if status == "rejected" else "",
    }
    prof = DoctorModel.update_by_user_id(doctor_id, updates)
    record_audit_log(
        g.current_user_id,
        f"DOCTOR_{status.upper()}",
        "doctor",
        doctor_id,
        {"rejection_reason": updates["rejection_reason"]},
    )
    return jsonify({"doctor": UserModel.to_public(user), "profile": DoctorModel.to_public(prof)}), 200


@admin_bp.get("/predictions")
@require_roles("admin")
def admin_predictions():
    disease = request.args.get("disease", "")
    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")
    search = request.args.get("search", "")
    patient_id = request.args.get("patient_id") or None
    records = query_predictions(
        patient_id=patient_id,
        search=search,
        disease=disease,
        start_date=start_date,
        end_date=end_date,
    )
    avg_conf = (
        round(sum(r.get("confidence_score", 0) for r in records) / len(records), 4)
        if records
        else 0.0
    )
    return jsonify({"predictions": records, "summary": {"total": len(records), "average_confidence": avg_conf}}), 200


@admin_bp.get("/consultations")
@require_roles("admin")
def admin_consultations():
    status = request.args.get("status", "")
    consultations = get_authorized_consultations(g.current_user_id, "admin", status_filter=status)
    return jsonify({"consultations": consultations}), 200


@admin_bp.put("/consultations/<consultation_id>")
@require_roles("admin")
def admin_manage_consultation(consultation_id: str):
    oid = parse_object_id(consultation_id)
    if oid is None:
        return jsonify({"error": "Invalid consultation ID."}), 400
    db = get_db()
    existing = db.consultations.find_one({"_id": oid})
    if not existing:
        return jsonify({"error": "Consultation not found."}), 404

    data = request.get_json(silent=True) or {}
    status = sanitize_text(data.get("consultation_status"), 30).lower()
    if status not in ("pending", "accepted", "rejected", "completed"):
        return jsonify({"error": "Invalid consultation status."}), 400

    db.consultations.update_one({"_id": oid}, {"$set": {"consultation_status": status}})
    record_audit_log(g.current_user_id, "ADMIN_UPDATED_CONSULTATION", "consultation", consultation_id, {"status": status})
    return jsonify({"message": "Consultation updated."}), 200


@admin_bp.get("/users")
@require_roles("admin")
def admin_users():
    db = get_db()
    role_filter = sanitize_text(request.args.get("role", ""), 20).lower()
    query = {"role": role_filter} if role_filter and role_filter != "all" else {}
    users = [UserModel.to_public(u) for u in db.users.find(query).sort("created_at", -1)]
    return jsonify({"users": users}), 200


@admin_bp.put("/users/<user_id>/status")
@require_roles("admin")
def admin_toggle_user_status(user_id: str):
    if user_id == g.current_user_id:
        return jsonify({"error": "You cannot deactivate your own administrator account."}), 400
    user = UserModel.find_by_id(user_id)
    if not user:
        return jsonify({"error": "User not found."}), 404

    data = request.get_json(silent=True) or {}
    status = sanitize_text(data.get("account_status"), 20).lower()
    if status not in ("active", "inactive"):
        return jsonify({"error": "account_status must be 'active' or 'inactive'."}), 400

    updated = UserModel.update_by_id(user_id, {"account_status": status})
    record_audit_log(g.current_user_id, f"USER_STATUS_{status.upper()}", "user", user_id)
    return jsonify({"user": UserModel.to_public(updated)}), 200


@admin_bp.get("/conversations")
@require_roles("admin")
def admin_conversation_metadata():
    """Return conversation metadata only; private message bodies are never exposed routinely."""
    db = get_db()
    convs = list(db.conversations.find({}).sort("last_message_at", -1))
    user_ids = {c["patient_id"] for c in convs} | {c["doctor_id"] for c in convs}
    oids = [ObjectId(uid) for uid in user_ids if ObjectId.is_valid(uid)]
    user_map = {str(u["_id"]): u["full_name"] for u in db.users.find({"_id": {"$in": oids}}, {"full_name": 1})}

    items = []
    for c in convs:
        cid = str(c["_id"])
        items.append(
            {
                "id": cid,
                "patient_id": c["patient_id"],
                "patient_name": user_map.get(c["patient_id"], "Patient"),
                "doctor_id": c["doctor_id"],
                "doctor_name": user_map.get(c["doctor_id"], "Doctor"),
                "last_message_at": c.get("last_message_at").isoformat() if c.get("last_message_at") else None,
                "created_at": c.get("created_at").isoformat() if c.get("created_at") else None,
                "message_count": db.messages.count_documents({"conversation_id": cid}),
                "reported": bool(c.get("reported", False)),
                "report_reason": c.get("report_reason", ""),
            }
        )
    return jsonify({"conversations": items}), 200


@admin_bp.get("/conversations/<conversation_id>/moderate")
@require_roles("admin")
def admin_moderate_reported_conversation(conversation_id: str):
    oid = parse_object_id(conversation_id)
    if oid is None:
        return jsonify({"error": "Invalid conversation ID."}), 400
    db = get_db()
    conv = db.conversations.find_one({"_id": oid})
    if not conv:
        return jsonify({"error": "Conversation not found."}), 404
    if not conv.get("reported"):
        return jsonify({"error": "Only reported conversations can be opened for moderation review."}), 403

    reason = sanitize_text(request.args.get("reason", ""), 300) or "Reported conversation moderation review"
    msgs = [serialize_doc(m) for m in db.messages.find({"conversation_id": conversation_id}).sort("sent_at", 1)]
    record_audit_log(
        g.current_user_id,
        "ADMIN_MODERATED_CONVERSATION",
        "conversation",
        conversation_id,
        {"reason": reason},
    )
    return jsonify({"conversation": serialize_doc(conv), "messages": msgs}), 200


@admin_bp.get("/audit-logs")
@require_roles("admin")
def admin_audit_logs():
    db = get_db()
    logs = [serialize_doc(l) for l in db.audit_logs.find({}).sort("timestamp", -1).limit(200)]
    return jsonify({"audit_logs": logs}), 200


@admin_bp.get("/settings")
@require_roles("admin")
def get_platform_settings():
    db = get_db()
    doc = db.platform_settings.find_one({"_id": "global"}) or {
        "_id": "global",
        "allow_patient_registration": True,
        "allow_doctor_registration": True,
        "require_doctor_verification": True,
        "max_upload_mb": 10,
        "clinical_disclaimer": (
            "Educational and clinical decision-support prototype. AI confidence scores "
            "are not confirmed disease probabilities."
        ),
    }
    return jsonify({"settings": serialize_doc(doc)}), 200


@admin_bp.put("/settings")
@require_roles("admin")
def update_platform_settings():
    db = get_db()
    data = request.get_json(silent=True) or {}
    updates = {
        "allow_patient_registration": bool(data.get("allow_patient_registration", True)),
        "allow_doctor_registration": bool(data.get("allow_doctor_registration", True)),
        "require_doctor_verification": bool(data.get("require_doctor_verification", True)),
        "max_upload_mb": max(1, min(50, int(data.get("max_upload_mb", 10)))),
        "clinical_disclaimer": sanitize_text(data.get("clinical_disclaimer"), 500)
        or "Educational and clinical decision-support prototype.",
    }
    db.platform_settings.update_one({"_id": "global"}, {"$set": updates}, upsert=True)
    record_audit_log(g.current_user_id, "ADMIN_UPDATED_SETTINGS", "settings", "global", updates)
    return jsonify({"settings": {"id": "global", **updates}}), 200
