from datetime import datetime, timezone
from typing import Any
from bson import ObjectId
from pymongo import ASCENDING, DESCENDING, MongoClient
from pymongo.errors import PyMongoError

_client = None
_db = None
_db_error = None


def parse_object_id(value: Any) -> ObjectId | None:
    if isinstance(value, ObjectId):
        return value
    if not isinstance(value, str) or not ObjectId.is_valid(value):
        return None
    return ObjectId(value)


def serialize_value(val: Any) -> Any:
    if isinstance(val, ObjectId):
        return str(val)
    if isinstance(val, datetime):
        if val.tzinfo is None:
            val = val.replace(tzinfo=timezone.utc)
        return val.isoformat()
    if isinstance(val, list):
        return [serialize_value(item) for item in val]
    if isinstance(val, dict):
        return {k: serialize_value(v) for k, v in val.items()}
    return val


def serialize_doc(doc: dict | None, exclude: set[str] | None = None) -> dict | None:
    if doc is None:
        return None
    result = {}
    skip = exclude or set()
    for key, value in doc.items():
        if key in skip:
            continue
        if key == "_id":
            result["id"] = str(value)
        else:
            result[key] = serialize_value(value)
    return result


def _ensure_indexes(db) -> None:
    db.users.create_index([("email", ASCENDING)], unique=True)
    db.users.create_index([("role", ASCENDING), ("account_status", ASCENDING)])

    db.patients.create_index([("user_id", ASCENDING)], unique=True)

    db.doctors.create_index([("user_id", ASCENDING)], unique=True)
    db.doctors.create_index([("registration_number", ASCENDING)], unique=True)
    db.doctors.create_index([("verification_status", ASCENDING)])

    db.predictions.create_index([("prediction_code", ASCENDING)], unique=True)
    db.predictions.create_index([("patient_id", ASCENDING), ("prediction_date", DESCENDING)])
    db.predictions.create_index([("predicted_class", ASCENDING), ("prediction_date", DESCENDING)])

    db.consultations.create_index([("patient_id", ASCENDING), ("requested_at", DESCENDING)])
    db.consultations.create_index([("doctor_id", ASCENDING), ("consultation_status", ASCENDING)])
    db.consultations.create_index([("prediction_id", ASCENDING)])

    db.conversations.create_index([("patient_id", ASCENDING), ("doctor_id", ASCENDING)], unique=True)
    db.conversations.create_index([("last_message_at", DESCENDING)])

    db.messages.create_index([("conversation_id", ASCENDING), ("sent_at", ASCENDING)])
    db.messages.create_index([("receiver_id", ASCENDING), ("read_at", ASCENDING)])

    db.audit_logs.create_index([("user_id", ASCENDING), ("timestamp", DESCENDING)])
    db.audit_logs.create_index([("timestamp", DESCENDING)])

    db.revoked_tokens.create_index([("jti", ASCENDING)], unique=True)
    db.staged_uploads.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])


def init_db(app) -> tuple[Any, str | None]:
    global _client, _db, _db_error
    mongo_uri = app.config.get("MONGO_URI", "").strip()
    db_name = app.config.get("DATABASE_NAME", "retinal_ai_db")

    if not mongo_uri:
        _client = None
        _db = None
        _db_error = "MONGO_URI is not configured in backend/.env."
        return None, _db_error

    try:
        if mongo_uri.startswith("mongomock://"):
            import mongomock

            _client = mongomock.MongoClient()
            _db = _client[db_name]
        else:
            _client = MongoClient(mongo_uri, serverSelectionTimeoutMS=3000)
            _client.admin.command("ping")
            _db = _client[db_name]

        _ensure_indexes(_db)
        _db_error = None
        return _db, None
    except Exception as exc:
        _client = None
        _db = None
        _db_error = f"MongoDB connection failed: {exc}"
        return None, _db_error


def reset_db_state() -> None:
    global _client, _db, _db_error
    _client = None
    _db = None
    _db_error = None


def get_db():
    return _db


def check_db_health(app=None) -> tuple[bool, str | None]:
    global _db, _db_error
    if _db is None and app is not None:
        init_db(app)
    if _db is None:
        return False, _db_error or "MongoDB is not connected."
    try:
        if _client is not None and hasattr(_client, "admin"):
            _client.admin.command("ping")
        return True, None
    except PyMongoError as exc:
        return False, f"MongoDB health check failed: {exc}"
