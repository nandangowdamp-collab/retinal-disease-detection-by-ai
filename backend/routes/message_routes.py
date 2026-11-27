from datetime import datetime, timezone
from flask import Blueprint, g, jsonify, request
from database.db import get_db, parse_object_id, serialize_doc
from services.message_service import (
    MessengerError,
    create_chat_message,
    get_conversation_messages,
    get_or_create_conversation,
    is_conversation_participant,
    list_conversations_for_user,
    mark_conversation_messages_read,
    mark_message_read,
)
from sockets.chat_socket import get_online_user_ids, emit_new_message
from utils.decorators import record_audit_log, require_roles
from utils.validators import sanitize_text

message_bp = Blueprint("messages", __name__, url_prefix="/api/messages")


def _ensure_messenger_access():
    role = g.current_user.get("role")
    if role == "doctor":
        doc = get_db().doctors.find_one({"user_id": g.current_user_id})
        if not doc or doc.get("verification_status") != "verified":
            return jsonify({"error": "Doctor verification required before using messenger."}), 403
    return None


@message_bp.get("/conversations")
@require_roles("patient", "doctor")
def get_conversations():
    err_resp = _ensure_messenger_access()
    if err_resp:
        return err_resp
    try:
        convs = list_conversations_for_user(
            g.current_user_id, g.current_user.get("role"), get_online_user_ids()
        )
        return jsonify({"conversations": convs}), 200
    except MessengerError as exc:
        return jsonify({"error": exc.message}), exc.status_code


@message_bp.post("/conversations")
@require_roles("patient", "doctor")
def start_conversation():
    err_resp = _ensure_messenger_access()
    if err_resp:
        return err_resp
    data = request.get_json(silent=True) or {}
    role = g.current_user.get("role")
    if role == "patient":
        patient_id = g.current_user_id
        doctor_id = sanitize_text(data.get("doctor_id"), 60)
    else:
        doctor_id = g.current_user_id
        patient_id = sanitize_text(data.get("patient_id"), 60)

    try:
        conv = get_or_create_conversation(patient_id, doctor_id)
        return jsonify({"conversation": serialize_doc(conv)}), 201
    except MessengerError as exc:
        return jsonify({"error": exc.message}), exc.status_code


@message_bp.get("/<conversation_id>")
@require_roles("patient", "doctor")
def get_messages(conversation_id: str):
    err_resp = _ensure_messenger_access()
    if err_resp:
        return err_resp
    try:
        conv, msgs = get_conversation_messages(conversation_id, g.current_user_id)
        mark_conversation_messages_read(conversation_id, g.current_user_id)
        return jsonify({"conversation": conv, "messages": msgs}), 200
    except MessengerError as exc:
        return jsonify({"error": exc.message}), exc.status_code


@message_bp.post("")
@require_roles("patient", "doctor")
def send_message():
    err_resp = _ensure_messenger_access()
    if err_resp:
        return err_resp
    data = request.get_json(silent=True) or {}
    conversation_id = sanitize_text(data.get("conversation_id"), 60)
    message_text = data.get("message", "")
    message_type = sanitize_text(data.get("message_type", "text"), 30)
    consultation_id = sanitize_text(data.get("consultation_id"), 60)

    try:
        msg = create_chat_message(
            conversation_id, g.current_user_id, message_text, message_type, consultation_id
        )
        emit_new_message(msg)
        return jsonify({"message": msg}), 201
    except MessengerError as exc:
        return jsonify({"error": exc.message}), exc.status_code


@message_bp.put("/<message_id>/read")
@require_roles("patient", "doctor")
def read_single_message(message_id: str):
    err_resp = _ensure_messenger_access()
    if err_resp:
        return err_resp
    try:
        msg = mark_message_read(message_id, g.current_user_id)
        return jsonify({"message": msg}), 200
    except MessengerError as exc:
        return jsonify({"error": exc.message}), exc.status_code


@message_bp.put("/conversations/<conversation_id>/read")
@require_roles("patient", "doctor")
def read_conversation(conversation_id: str):
    err_resp = _ensure_messenger_access()
    if err_resp:
        return err_resp
    try:
        count = mark_conversation_messages_read(conversation_id, g.current_user_id)
        return jsonify({"marked_read": count}), 200
    except MessengerError as exc:
        return jsonify({"error": exc.message}), exc.status_code


@message_bp.post("/conversations/<conversation_id>/report")
@require_roles("patient", "doctor")
def report_conversation(conversation_id: str):
    oid = parse_object_id(conversation_id)
    if oid is None:
        return jsonify({"error": "Invalid conversation ID."}), 400
    db = get_db()
    conv = db.conversations.find_one({"_id": oid})
    if not conv or not is_conversation_participant(conv, g.current_user_id):
        return jsonify({"error": "Conversation not found or unauthorized."}), 403

    reason = sanitize_text((request.get_json(silent=True) or {}).get("reason"), 500)
    if not reason:
        return jsonify({"error": "Please provide a reason for reporting this conversation."}), 400

    db.conversations.update_one(
        {"_id": oid},
        {
            "$set": {
                "reported": True,
                "report_reason": reason,
                "reported_by": g.current_user_id,
                "reported_at": datetime.now(timezone.utc),
            }
        },
    )
    record_audit_log(g.current_user_id, "CONVERSATION_REPORTED", "conversation", conversation_id, {"reason": reason})
    return jsonify({"message": "Conversation reported for moderator review."}), 200
