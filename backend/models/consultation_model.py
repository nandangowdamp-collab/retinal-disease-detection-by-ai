from datetime import datetime, timezone
from database.db import get_db, parse_object_id, serialize_doc


class ConsultationModel:
    @staticmethod
    def create(
        patient_id: str,
        doctor_id: str,
        prediction_id: str | None,
        consultation_reason: str,
    ) -> dict:
        now = datetime.now(timezone.utc)
        doc = {
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "prediction_id": prediction_id or "",
            "consultation_reason": consultation_reason.strip(),
            "consultation_notes": "",
            "recommendations": "",
            "rejection_reason": "",
            "consultation_status": "pending",
            "scheduled_at": None,
            "requested_at": now,
            "updated_at": now,
        }
        result = get_db().consultations.insert_one(doc)
        doc["_id"] = result.inserted_id
        return doc

    @staticmethod
    def find_by_id(consultation_id: str) -> dict | None:
        oid = parse_object_id(consultation_id)
        if oid is None:
            return None
        return get_db().consultations.find_one({"_id": oid})

    @staticmethod
    def update_by_id(consultation_id: str, updates: dict) -> dict | None:
        oid = parse_object_id(consultation_id)
        if oid is None:
            return None
        updates["updated_at"] = datetime.now(timezone.utc)
        get_db().consultations.update_one({"_id": oid}, {"$set": updates})
        return get_db().consultations.find_one({"_id": oid})

    @staticmethod
    def to_public(doc: dict | None) -> dict | None:
        return serialize_doc(doc)
