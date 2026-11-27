from flask import request
from flask_jwt_extended import decode_token
from flask_socketio import emit, join_room, leave_room

from database.db import get_db, parse_object_id
from services.message_service import (
    MessengerError,
    create_chat_message,
    is_conversation_participant,
    mark_conversation_messages_read,
)

_socketio = None
_sid_to_user: dict[str, str] = {}
_user_sids: dict[str, set[str]] = {}


def get_online_user_ids() -> set[str]:
    return {uid for uid, sids in _user_sids.items() if sids}


def emit_new_message(message_doc: dict) -> None:
    if _socketio is None:
        return
    conv_id = message_doc.get("conversation_id")
    receiver_id = message_doc.get("receiver_id")
    sender_id = message_doc.get("sender_id")
    if conv_id:
        _socketio.emit("new_message", message_doc, room=f"conv:{conv_id}")
    if receiver_id:
        _socketio.emit("message_notification", message_doc, room=f"user:{receiver_id}")
    if sender_id:
        _socketio.emit("message_notification", message_doc, room=f"user:{sender_id}")


def _authenticate_socket(auth_payload=None) -> str | None:
    token = None
    if isinstance(auth_payload, dict):
        token = auth_payload.get("token")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1].strip()
    if not token:
        token = request.args.get("token")
    if not token:
        return None

    try:
        decoded = decode_token(token)
    except Exception:
        return None

    db = get_db()
    if db is None:
        return None
    if db.revoked_tokens.find_one({"jti": decoded.get("jti")}):
        return None

    user_id = decoded.get("sub")
    oid = parse_object_id(user_id)
    if oid is None:
        return None

    user = db.users.find_one({"_id": oid})
    if not user or user.get("account_status") != "active":
        return None

    role = user.get("role")
    if role == "doctor":
        doc = db.doctors.find_one({"user_id": user_id})
        if not doc or doc.get("verification_status") != "verified":
            return None
    elif role != "patient":
        return None

    return user_id


def register_socket_handlers(socketio):
    global _socketio
    _socketio = socketio

    @socketio.on("connect")
    def handle_connect(auth=None):
        user_id = _authenticate_socket(auth)
        if not user_id:
            return False

        sid = request.sid
        _sid_to_user[sid] = user_id
        _user_sids.setdefault(user_id, set()).add(sid)
        join_room(f"user:{user_id}")
        emit("presence_update", {"user_id": user_id, "online": True}, broadcast=True)
        return True

    @socketio.on("disconnect")
    def handle_disconnect():
        sid = request.sid
        user_id = _sid_to_user.pop(sid, None)
        if not user_id:
            return
        sids = _user_sids.get(user_id, set())
        sids.discard(sid)
        if not sids:
            _user_sids.pop(user_id, None)
            emit("presence_update", {"user_id": user_id, "online": False}, broadcast=True)

    @socketio.on("join_conversation")
    def handle_join_conversation(data):
        user_id = _sid_to_user.get(request.sid)
        conv_id = (data or {}).get("conversation_id", "")
        oid = parse_object_id(conv_id)
        if not user_id or oid is None:
            return {"error": "Unauthorized"}

        conv = get_db().conversations.find_one({"_id": oid})
        if not is_conversation_participant(conv, user_id):
            return {"error": "Unauthorized"}

        join_room(f"conv:{conv_id}")
        return {"joined": conv_id}

    @socketio.on("leave_conversation")
    def handle_leave_conversation(data):
        conv_id = (data or {}).get("conversation_id", "")
        if conv_id:
            leave_room(f"conv:{conv_id}")

    @socketio.on("send_message")
    def handle_send_message(data):
        user_id = _sid_to_user.get(request.sid)
        if not user_id:
            return {"error": "Authentication required."}
        payload = data or {}
        try:
            msg = create_chat_message(
                conversation_id=str(payload.get("conversation_id", "")),
                sender_id=user_id,
                message_text=str(payload.get("message", "")),
                message_type=str(payload.get("message_type", "text")),
                consultation_id=str(payload.get("consultation_id", "")),
            )
            emit_new_message(msg)
            return {"message": msg}
        except MessengerError as exc:
            return {"error": exc.message}

    @socketio.on("mark_read")
    def handle_mark_read(data):
        user_id = _sid_to_user.get(request.sid)
        conv_id = str((data or {}).get("conversation_id", ""))
        if not user_id or not conv_id:
            return {"error": "Unauthorized"}
        try:
            count = mark_conversation_messages_read(conv_id, user_id)
            emit("messages_read", {"conversation_id": conv_id, "reader_id": user_id, "count": count}, room=f"conv:{conv_id}")
            return {"marked_read": count}
        except MessengerError as exc:
            return {"error": exc.message}

    @socketio.on("typing")
    def handle_typing(data):
        user_id = _sid_to_user.get(request.sid)
        conv_id = str((data or {}).get("conversation_id", ""))
        oid = parse_object_id(conv_id)
        if not user_id or oid is None:
            return
        conv = get_db().conversations.find_one({"_id": oid})
        if not is_conversation_participant(conv, user_id):
            return
        emit(
            "typing",
            {"conversation_id": conv_id, "user_id": user_id, "is_typing": bool((data or {}).get("is_typing"))},
            room=f"conv:{conv_id}",
            include_self=False,
        )
