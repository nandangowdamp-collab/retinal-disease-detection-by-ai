from datetime import datetime, timezone
from bson import ObjectId

from database.db import get_db, parse_object_id, serialize_doc


class MessengerError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def is_conversation_participant(conversation_doc: dict | None, user_id: str) -> bool:
    if not conversation_doc:
        return False
    return user_id in (conversation_doc.get("patient_id"), conversation_doc.get("doctor_id"))


def get_or_create_conversation(patient_id: str, doctor_id: str) -> dict:
    db = get_db()
    if not ObjectId.is_valid(patient_id) or not ObjectId.is_valid(doctor_id):
        raise MessengerError("Invalid participant ID.", 400)

    patient = db.users.find_one({"_id": ObjectId(patient_id), "role": "patient", "account_status": "active"})
    if not patient:
        raise MessengerError("Patient account not found or inactive.", 404)

    doctor = db.users.find_one({"_id": ObjectId(doctor_id), "role": "doctor", "account_status": "active"})
    doctor_profile = db.doctors.find_one({"user_id": doctor_id, "verification_status": "verified"})
    if not doctor or not doctor_profile:
        raise MessengerError("Doctor not found or not verified.", 404)

    existing = db.conversations.find_one({"patient_id": patient_id, "doctor_id": doctor_id})
    if existing:
        return existing

    now = datetime.now(timezone.utc)
    doc = {
        "patient_id": patient_id,
        "doctor_id": doctor_id,
        "last_message": "",
        "last_message_at": now,
        "created_at": now,
        "reported": False,
        "report_reason": "",
    }
    result = db.conversations.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


def list_conversations_for_user(user_id: str, role: str, online_users: set[str] | None = None) -> list[dict]:
    db = get_db()
    online = online_users or set()

    if role == "patient":
        query = {"patient_id": user_id}
    elif role == "doctor":
        query = {"doctor_id": user_id}
    else:
        raise MessengerError("Only patients and doctors can access personal conversations.", 403)

    convs = list(db.conversations.find(query).sort("last_message_at", -1))
    other_ids = [c["doctor_id"] if role == "patient" else c["patient_id"] for c in convs]
    oids = [ObjectId(oid) for oid in other_ids if ObjectId.is_valid(oid)]

    user_map = {}
    if oids:
        for u in db.users.find({"_id": {"$in": oids}}, {"full_name": 1, "email": 1, "role": 1}):
            user_map[str(u["_id"])] = u

    doc_map = {}
    if role == "patient" and other_ids:
        for dp in db.doctors.find({"user_id": {"$in": other_ids}}):
            doc_map[dp["user_id"]] = dp

    results = []
    for conv in convs:
        conv_id = str(conv["_id"])
        other_id = conv["doctor_id"] if role == "patient" else conv["patient_id"]
        other_user = user_map.get(other_id, {})
        unread_count = db.messages.count_documents(
            {"conversation_id": conv_id, "receiver_id": user_id, "read_at": None}
        )
        item = serialize_doc(conv)
        item["other_user"] = {
            "id": other_id,
            "full_name": other_user.get("full_name", "User"),
            "email": other_user.get("email", ""),
            "role": other_user.get("role", "doctor" if role == "patient" else "patient"),
            "specialization": doc_map.get(other_id, {}).get("specialization", ""),
            "online": other_id in online,
        }
        item["unread_count"] = unread_count
        results.append(item)
    return results


def get_conversation_messages(conversation_id: str, user_id: str) -> tuple[dict, list[dict]]:
    db = get_db()
    oid = parse_object_id(conversation_id)
    if oid is None:
        raise MessengerError("Invalid conversation ID.", 400)
    conv = db.conversations.find_one({"_id": oid})
    if not conv:
        raise MessengerError("Conversation not found.", 404)
    if not is_conversation_participant(conv, user_id):
        raise MessengerError("You are not authorized to view this conversation.", 403)

    msgs = list(db.messages.find({"conversation_id": conversation_id}).sort("sent_at", 1))
    return serialize_doc(conv), [serialize_doc(m) for m in msgs]


def create_chat_message(
    conversation_id: str,
    sender_id: str,
    message_text: str,
    message_type: str = "text",
    consultation_id: str = "",
) -> dict:
    db = get_db()
    oid = parse_object_id(conversation_id)
    if oid is None:
        raise MessengerError("Invalid conversation ID.", 400)
    conv = db.conversations.find_one({"_id": oid})
    if not conv:
        raise MessengerError("Conversation not found.", 404)
    if not is_conversation_participant(conv, sender_id):
        raise MessengerError("You are not authorized to send messages in this conversation.", 403)

    text = (message_text or "").strip()
    if not text:
        raise MessengerError("Message text cannot be empty.", 400)
    if len(text) > 2000:
        raise MessengerError("Message cannot exceed 2000 characters.", 400)

    receiver_id = conv["doctor_id"] if sender_id == conv["patient_id"] else conv["patient_id"]
    now = datetime.now(timezone.utc)
    msg_doc = {
        "conversation_id": conversation_id,
        "sender_id": sender_id,
        "receiver_id": receiver_id,
        "message": text,
        "message_type": message_type if message_type in ("text", "consultation") else "text",
        "consultation_id": consultation_id or "",
        "sent_at": now,
        "read_at": None,
    }
    res = db.messages.insert_one(msg_doc)
    msg_doc["_id"] = res.inserted_id

    db.conversations.update_one(
        {"_id": oid},
        {"$set": {"last_message": text[:160], "last_message_at": now}},
    )
    return serialize_doc(msg_doc)


def mark_message_read(message_id: str, user_id: str) -> dict:
    db = get_db()
    oid = parse_object_id(message_id)
    if oid is None:
        raise MessengerError("Invalid message ID.", 400)
    msg = db.messages.find_one({"_id": oid})
    if not msg:
        raise MessengerError("Message not found.", 404)
    if msg.get("receiver_id") != user_id:
        raise MessengerError("Only the message recipient can mark a message as read.", 403)

    now = datetime.now(timezone.utc)
    if msg.get("read_at") is None:
        db.messages.update_one({"_id": oid}, {"$set": {"read_at": now}})
        msg["read_at"] = now
    return serialize_doc(msg)


def mark_conversation_messages_read(conversation_id: str, user_id: str) -> int:
    db = get_db()
    oid = parse_object_id(conversation_id)
    if oid is None:
        raise MessengerError("Invalid conversation ID.", 400)
    conv = db.conversations.find_one({"_id": oid})
    if not conv or not is_conversation_participant(conv, user_id):
        raise MessengerError("Not authorized for this conversation.", 403)

    now = datetime.now(timezone.utc)
    res = db.messages.update_many(
        {"conversation_id": conversation_id, "receiver_id": user_id, "read_at": None},
        {"$set": {"read_at": now}},
    )
    return int(res.modified_count)
