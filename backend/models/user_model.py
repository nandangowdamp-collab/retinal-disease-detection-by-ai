from datetime import datetime, timezone
from werkzeug.security import check_password_hash, generate_password_hash
from database.db import get_db, parse_object_id, serialize_doc


class UserModel:
    @staticmethod
    def create(full_name: str, email: str, phone: str, password: str, role: str, account_status: str = "active") -> dict:
        now = datetime.now(timezone.utc)
        doc = {
            "full_name": full_name.strip(),
            "email": email.strip().lower(),
            "phone": phone.strip(),
            "password_hash": generate_password_hash(password),
            "role": role,
            "account_status": account_status,
            "created_at": now,
            "updated_at": now,
        }
        result = get_db().users.insert_one(doc)
        doc["_id"] = result.inserted_id
        return doc

    @staticmethod
    def find_by_email(email: str) -> dict | None:
        return get_db().users.find_one({"email": email.strip().lower()})

    @staticmethod
    def find_by_id(user_id: str) -> dict | None:
        oid = parse_object_id(user_id)
        if oid is None:
            return None
        return get_db().users.find_one({"_id": oid})

    @staticmethod
    def verify_password(user_doc: dict, password: str) -> bool:
        return check_password_hash(user_doc.get("password_hash", ""), password)

    @staticmethod
    def update_by_id(user_id: str, updates: dict) -> dict | None:
        oid = parse_object_id(user_id)
        if oid is None:
            return None
        updates["updated_at"] = datetime.now(timezone.utc)
        get_db().users.update_one({"_id": oid}, {"$set": updates})
        return get_db().users.find_one({"_id": oid})

    @staticmethod
    def to_public(user_doc: dict | None) -> dict | None:
        return serialize_doc(user_doc, exclude={"password_hash"})
