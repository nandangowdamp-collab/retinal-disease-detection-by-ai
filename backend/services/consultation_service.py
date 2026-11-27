from datetime import datetime, timezone
from bson import ObjectId

from database.db import get_db
from models.consultation_model import ConsultationModel
from models.prediction_model import PredictionModel
from utils.decorators import record_audit_log
from utils.validators import sanitize_text


class ConsultationError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _enrich_consultations(docs: list[dict]) -> list[dict]:
    db = get_db()
    user_ids = set()
    pred_ids = set()
    for d in docs:
        if d.get("patient_id"):
            user_ids.add(d["patient_id"])
        if d.get("doctor_id"):
            user_ids.add(d["doctor_id"])
        if d.get("prediction_id"):
            pred_ids.add(d["prediction_id"])

    user_map = {}
    oids = [ObjectId(uid) for uid in user_ids if ObjectId.is_valid(uid)]
    if oids:
        for u in db.users.find({"_id": {"$in": oids}}, {"full_name": 1, "email": 1, "phone": 1}):
            user_map[str(u["_id"])] = u

    doc_prof_map = {}
    if user_ids:
        for dp in db.doctors.find({"user_id": {"$in": list(user_ids)}}):
            doc_prof_map[dp["user_id"]] = dp

    pred_map = {}
    pred_oids = [ObjectId(pid) for pid in pred_ids if ObjectId.is_valid(pid)]
    if pred_oids:
        for pr in db.predictions.find({"_id": {"$in": pred_oids}}):
            pred_map[str(pr["_id"])] = PredictionModel.to_public(pr)

    enriched = []
    for d in docs:
        pub = ConsultationModel.to_public(d)
        patient = user_map.get(d.get("patient_id"), {})
        doctor = user_map.get(d.get("doctor_id"), {})
        doc_prof = doc_prof_map.get(d.get("doctor_id"), {})
        pub["patient_name"] = patient.get("full_name", "Patient")
        pub["patient_email"] = patient.get("email", "")
        pub["doctor_name"] = doctor.get("full_name", "Doctor")
        pub["doctor_specialization"] = doc_prof.get("specialization", "")
        pub["doctor_hospital"] = doc_prof.get("hospital_name", "")
        pub["prediction"] = pred_map.get(d.get("prediction_id"))
        enriched.append(pub)
    return enriched


def create_consultation(patient_id: str, data: dict) -> dict:
    db = get_db()
    doctor_id = sanitize_text(data.get("doctor_id"), 60)
    reason = sanitize_text(data.get("consultation_reason"), 1000)
    prediction_id = sanitize_text(data.get("prediction_id"), 60)

    if not doctor_id:
        raise ConsultationError("Doctor selection is required.", 400)
    if not reason:
        raise ConsultationError("Consultation reason is required.", 400)
    if not ObjectId.is_valid(doctor_id):
        raise ConsultationError("Invalid doctor ID.", 400)

    doctor_user = db.users.find_one({"_id": ObjectId(doctor_id), "role": "doctor", "account_status": "active"})
    doctor_profile = db.doctors.find_one({"user_id": doctor_id, "verification_status": "verified"})
    if not doctor_user or not doctor_profile:
        raise ConsultationError("Selected doctor is unavailable or not verified.", 404)

    resolved_pred_id = ""
    if prediction_id:
        pred = PredictionModel.find_by_id(prediction_id)
        if not pred or pred.get("patient_id") != patient_id:
            raise ConsultationError("Referenced prediction record not found for this patient.", 404)
        resolved_pred_id = str(pred["_id"])

    doc = ConsultationModel.create(patient_id, doctor_id, resolved_pred_id, reason)
    record_audit_log(patient_id, "CONSULTATION_REQUESTED", "consultation", str(doc["_id"]))
    return _enrich_consultations([doc])[0]


def get_authorized_consultations(user_id: str, role: str, status_filter: str = "") -> list[dict]:
    db = get_db()
    query: dict = {}
    if role == "patient":
        query["patient_id"] = user_id
    elif role == "doctor":
        query["doctor_id"] = user_id
    elif role != "admin":
        raise ConsultationError("Unauthorized role.", 403)

    if status_filter and status_filter.lower() != "all":
        query["consultation_status"] = status_filter.lower()

    docs = list(db.consultations.find(query).sort("requested_at", -1))
    return _enrich_consultations(docs)


def update_consultation_by_doctor(consultation_id: str, doctor_id: str, data: dict) -> dict:
    consultation = ConsultationModel.find_by_id(consultation_id)
    if not consultation:
        raise ConsultationError("Consultation not found.", 404)
    if consultation.get("doctor_id") != doctor_id:
        raise ConsultationError("You are not assigned to this consultation.", 403)

    updates: dict = {}
    new_status = sanitize_text(data.get("consultation_status"), 30).lower()
    if new_status:
        allowed = {"pending", "accepted", "rejected", "completed"}
        if new_status not in allowed:
            raise ConsultationError(f"Invalid status. Allowed: {sorted(allowed)}", 400)
        if new_status == "rejected":
            rej_reason = sanitize_text(data.get("rejection_reason"), 500)
            if not rej_reason:
                raise ConsultationError("Please provide a reason when rejecting a consultation.", 400)
            updates["rejection_reason"] = rej_reason
        updates["consultation_status"] = new_status

    if "consultation_notes" in data:
        updates["consultation_notes"] = sanitize_text(data.get("consultation_notes"), 2000)
    if "recommendations" in data:
        updates["recommendations"] = sanitize_text(data.get("recommendations"), 2000)
    if data.get("scheduled_at"):
        updates["scheduled_at"] = sanitize_text(data.get("scheduled_at"), 64)

    if not updates:
        raise ConsultationError("No valid updates supplied.", 400)

    updated = ConsultationModel.update_by_id(consultation_id, updates)

    # Ensure conversation exists when accepted
    if updates.get("consultation_status") == "accepted":
        db = get_db()
        now = datetime.now(timezone.utc)
        db.conversations.update_one(
            {"patient_id": consultation["patient_id"], "doctor_id": doctor_id},
            {
                "$setOnInsert": {
                    "patient_id": consultation["patient_id"],
                    "doctor_id": doctor_id,
                    "last_message": "",
                    "last_message_at": now,
                    "created_at": now,
                    "reported": False,
                }
            },
            upsert=True,
        )

    record_audit_log(
        doctor_id,
        "CONSULTATION_UPDATED",
        "consultation",
        consultation_id,
        {"status": updated.get("consultation_status")},
    )
    return _enrich_consultations([updated])[0]
