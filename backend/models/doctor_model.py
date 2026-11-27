from database.db import get_db, serialize_doc


class DoctorModel:
    @staticmethod
    def create(
        user_id: str,
        qualification: str,
        specialization: str,
        registration_number: str,
        experience: int,
        hospital_name: str,
        verification_status: str = "pending",
        availability: str = "Mon - Fri, 09:00 AM - 05:00 PM",
    ) -> dict:
        doc = {
            "user_id": user_id,
            "qualification": qualification.strip(),
            "specialization": specialization.strip(),
            "registration_number": registration_number.strip(),
            "experience": int(experience),
            "hospital_name": hospital_name.strip(),
            "verification_status": verification_status,
            "rejection_reason": "",
            "availability": availability,
        }
        result = get_db().doctors.insert_one(doc)
        doc["_id"] = result.inserted_id
        return doc

    @staticmethod
    def find_by_user_id(user_id: str) -> dict | None:
        return get_db().doctors.find_one({"user_id": user_id})

    @staticmethod
    def find_by_registration_number(registration_number: str) -> dict | None:
        return get_db().doctors.find_one({"registration_number": registration_number.strip()})

    @staticmethod
    def update_by_user_id(user_id: str, updates: dict) -> dict | None:
        get_db().doctors.update_one({"user_id": user_id}, {"$set": updates})
        return get_db().doctors.find_one({"user_id": user_id})

    @staticmethod
    def to_public(doc: dict | None) -> dict | None:
        return serialize_doc(doc)
