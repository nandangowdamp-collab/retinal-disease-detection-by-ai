from datetime import datetime, timezone
from database.db import get_db, serialize_doc


class PatientModel:
    @staticmethod
    def create(user_id: str, age: int, gender: str, address: str, profile_image: str = "") -> dict:
        doc = {
            "user_id": user_id,
            "age": int(age),
            "gender": gender.strip(),
            "address": address.strip(),
            "profile_image": profile_image,
            "created_at": datetime.now(timezone.utc),
        }
        result = get_db().patients.insert_one(doc)
        doc["_id"] = result.inserted_id
        return doc

    @staticmethod
    def find_by_user_id(user_id: str) -> dict | None:
        return get_db().patients.find_one({"user_id": user_id})

    @staticmethod
    def update_by_user_id(user_id: str, updates: dict) -> dict | None:
        get_db().patients.update_one({"user_id": user_id}, {"$set": updates})
        return get_db().patients.find_one({"user_id": user_id})

    @staticmethod
    def to_public(doc: dict | None) -> dict | None:
        return serialize_doc(doc)
