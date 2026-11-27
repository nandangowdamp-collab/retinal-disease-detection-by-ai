from datetime import datetime, timezone
import uuid
from database.db import get_db, parse_object_id, serialize_doc


class PredictionModel:
    @staticmethod
    def create(
        patient_id: str,
        image_path: str,
        original_filename: str,
        predicted_class: str,
        confidence_score: float,
        class_scores: dict,
        model_version: str,
    ) -> dict:
        now = datetime.now(timezone.utc)
        code = f"PRED-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        doc = {
            "prediction_code": code,
            "patient_id": patient_id,
            "image_path": image_path,
            "original_filename": original_filename,
            "predicted_class": predicted_class,
            "confidence_score": float(confidence_score),
            "class_scores": {k: float(v) for k, v in class_scores.items()},
            "model_version": model_version,
            "prediction_status": "Completed",
            "doctor_assessment": None,
            "prediction_date": now,
        }
        result = get_db().predictions.insert_one(doc)
        doc["_id"] = result.inserted_id
        return doc

    @staticmethod
    def find_by_id(prediction_id: str) -> dict | None:
        oid = parse_object_id(prediction_id)
        if oid is not None:
            doc = get_db().predictions.find_one({"_id": oid})
            if doc:
                return doc
        return get_db().predictions.find_one({"prediction_code": prediction_id})

    @staticmethod
    def to_public(doc: dict | None) -> dict | None:
        if doc is None:
            return None
        data = serialize_doc(doc, exclude={"image_path"})
        data["prediction_id"] = data.get("prediction_code") or data.get("id")
        data["image_url"] = f"/api/prediction/{data['id']}/image"
        return data
