from datetime import datetime, timezone
from functools import wraps
from flask import current_app, g, jsonify
from flask_jwt_extended import get_jwt, get_jwt_identity, verify_jwt_in_request

from database.db import check_db_health, get_db, parse_object_id


def record_audit_log(user_id: str | None, action: str, resource_type: str, resource_id: str | None = None, details: dict | None = None) -> None:
    db = get_db()
    if db is None:
        return
    db.audit_logs.insert_one(
        {
            "user_id": user_id,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "details": details or {},
            "timestamp": datetime.now(timezone.utc),
        }
    )


def require_db(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        ok, err = check_db_health(current_app)
        if not ok:
            return (
                jsonify(
                    {
                        "error": "Database unavailable",
                        "message": err or "MongoDB is not configured or reachable.",
                    }
                ),
                503,
            )
        return fn(*args, **kwargs)

    return wrapper


def require_roles(*roles: str):
    def decorator(fn):
        @wraps(fn)
        @require_db
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            user_id = get_jwt_identity()
            db = get_db()

            if db.revoked_tokens.find_one({"jti": claims.get("jti")}):
                return jsonify({"error": "Token has been revoked. Please log in again."}), 401

            oid = parse_object_id(user_id)
            if oid is None:
                return jsonify({"error": "Invalid authentication identity."}), 401

            user = db.users.find_one({"_id": oid})
            if not user:
                return jsonify({"error": "User account not found."}), 401
            if user.get("account_status") != "active":
                return jsonify({"error": "Your account is deactivated. Contact administrator."}), 403
            if roles and user.get("role") not in roles:
                return jsonify({"error": "You are not authorized to access this resource."}), 403

            g.current_user = user
            g.current_user_id = str(user["_id"])
            g.current_claims = claims
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def require_verified_doctor(fn):
    @wraps(fn)
    @require_roles("doctor")
    def wrapper(*args, **kwargs):
        db = get_db()
        doctor = db.doctors.find_one({"user_id": g.current_user_id})
        if not doctor:
            return jsonify({"error": "Doctor profile not found."}), 404
        status = doctor.get("verification_status", "pending")
        if status != "verified":
            return (
                jsonify(
                    {
                        "error": "Doctor verification required",
                        "verification_status": status,
                        "message": "Your doctor account must be verified by an administrator before accessing patient records or consultations.",
                    }
                ),
                403,
            )
        g.current_doctor = doctor
        return fn(*args, **kwargs)

    return wrapper
