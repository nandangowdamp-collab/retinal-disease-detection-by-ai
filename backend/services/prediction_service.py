from datetime import datetime, timedelta, timezone
from bson import ObjectId

from ai_model.predictor import ModelUnavailableError, get_predictor
from database.db import get_db, parse_object_id
from models.prediction_model import PredictionModel
from services.image_service import ImageValidationError, resolve_upload_path, validate_and_save_retinal_image


class PredictionServiceError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def stage_retinal_upload(user_id: str, file_storage, app_config: dict) -> dict:
    try:
        stored_name, original_name = validate_and_save_retinal_image(
            file_storage,
            app_config["UPLOAD_FOLDER"],
            app_config["MAX_CONTENT_LENGTH"],
        )
    except ImageValidationError as exc:
        raise PredictionServiceError(str(exc), 400) from exc

    doc = {
        "user_id": user_id,
        "image_path": stored_name,
        "original_filename": original_name,
        "created_at": datetime.now(timezone.utc),
    }
    result = get_db().staged_uploads.insert_one(doc)
    return {
        "upload_id": str(result.inserted_id),
        "original_filename": original_name,
        "message": "Retinal image uploaded and validated.",
    }


def classify_retinal_image(user_id: str, file_storage, upload_id: str | None, app_config: dict) -> dict:
    db = get_db()
    newly_saved = False
    staged_doc = None

    if file_storage is not None and file_storage.filename:
        try:
            stored_name, original_name = validate_and_save_retinal_image(
                file_storage,
                app_config["UPLOAD_FOLDER"],
                app_config["MAX_CONTENT_LENGTH"],
            )
            newly_saved = True
        except ImageValidationError as exc:
            raise PredictionServiceError(str(exc), 400) from exc
    elif upload_id:
        oid = parse_object_id(upload_id)
        if oid is None:
            raise PredictionServiceError("Invalid upload_id.", 400)
        staged_doc = db.staged_uploads.find_one({"_id": oid, "user_id": user_id})
        if not staged_doc:
            raise PredictionServiceError("Staged upload not found.", 404)
        stored_name = staged_doc["image_path"]
        original_name = staged_doc["original_filename"]
    else:
        raise PredictionServiceError("Provide a retinal image file or upload_id to classify.", 400)

    full_path = resolve_upload_path(app_config["UPLOAD_FOLDER"], stored_name)
    predictor = get_predictor(app_config["MODEL_PATH"], app_config["MODEL_CONFIG_PATH"])

    try:
        result = predictor.predict(full_path)
    except ModelUnavailableError as exc:
        # Clean up newly uploaded file so unpredicted images are not persisted
        if newly_saved and full_path.exists():
            full_path.unlink(missing_ok=True)
        raise PredictionServiceError(str(exc), 503) from exc
    except Exception as exc:
        if newly_saved and full_path.exists():
            full_path.unlink(missing_ok=True)
        raise PredictionServiceError(f"Retinal classification failed: {exc}", 400) from exc

    prediction_doc = PredictionModel.create(
        patient_id=user_id,
        image_path=stored_name,
        original_filename=original_name,
        predicted_class=result["predicted_class"],
        confidence_score=result["confidence_score"],
        class_scores=result["class_scores"],
        model_version=result["model_version"],
    )

    if staged_doc is not None:
        db.staged_uploads.delete_one({"_id": staged_doc["_id"]})

    return PredictionModel.to_public(prediction_doc)


def _parse_iso_date(date_str: str, end_of_day: bool = False) -> datetime | None:
    if not date_str:
        return None
    try:
        dt = datetime.fromisoformat(date_str.strip())
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        if end_of_day and len(date_str.strip()) <= 10:
            dt = dt + timedelta(days=1) - timedelta(microseconds=1)
        return dt
    except ValueError:
        return None


def query_predictions(
    patient_id: str | None = None,
    search: str = "",
    disease: str = "",
    start_date: str = "",
    end_date: str = "",
    limit: int = 200,
) -> list[dict]:
    db = get_db()
    query: dict = {}
    if patient_id:
        query["patient_id"] = patient_id
    if disease and disease.lower() != "all":
        query["predicted_class"] = disease
    if search:
        term = search.strip()
        query["$or"] = [
            {"prediction_code": {"$regex": term, "$options": "i"}},
            {"predicted_class": {"$regex": term, "$options": "i"}},
            {"original_filename": {"$regex": term, "$options": "i"}},
        ]

    start_dt = _parse_iso_date(start_date, end_of_day=False)
    end_dt = _parse_iso_date(end_date, end_of_day=True)
    if start_dt or end_dt:
        date_filter = {}
        if start_dt:
            date_filter["$gte"] = start_dt
        if end_dt:
            date_filter["$lte"] = end_dt
        query["prediction_date"] = date_filter

    cursor = db.predictions.find(query).sort("prediction_date", -1).limit(limit)
    docs = list(cursor)

    # Enrich with patient basic info when available
    patient_ids = list({d["patient_id"] for d in docs if d.get("patient_id")})
    user_map = {}
    if patient_ids:
        oids = [ObjectId(pid) for pid in patient_ids if ObjectId.is_valid(pid)]
        for u in db.users.find({"_id": {"$in": oids}}, {"full_name": 1, "email": 1}):
            user_map[str(u["_id"])] = {"full_name": u["full_name"], "email": u["email"]}

    results = []
    for doc in docs:
        pub = PredictionModel.to_public(doc)
        u_info = user_map.get(doc.get("patient_id"), {})
        pub["patient_name"] = u_info.get("full_name", "Unknown")
        pub["patient_email"] = u_info.get("email", "")
        results.append(pub)
    return results
