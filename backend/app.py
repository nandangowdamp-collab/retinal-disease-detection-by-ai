from datetime import timedelta
from pathlib import Path
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_socketio import SocketIO

from ai_model.predictor import get_predictor
from config import Config
from database.db import check_db_health, init_db
from routes import register_blueprints
from sockets import register_socket_handlers

socketio = SocketIO()


def create_app(test_config: dict | None = None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(
        hours=int(app.config.get("JWT_ACCESS_TOKEN_EXPIRES_HOURS", 24))
    )

    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)

    CORS(
        app,
        resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}},
        supports_credentials=True,
    )

    JWTManager(app)

    limiter = Limiter(
        key_func=get_remote_address,
        app=app,
        storage_uri=app.config.get("RATE_LIMIT_STORAGE_URI", "memory://"),
        enabled=not app.config.get("TESTING", False),
        default_limits=[],
    )
    app.extensions["limiter"] = limiter

    init_db(app)
    register_blueprints(app)

    # Apply strict rate limits on authentication endpoints
    limiter.limit("20 per minute")(app.view_functions["auth.login"])
    limiter.limit("10 per minute")(app.view_functions["auth.register"])

    @app.get("/api/health")
    def health():
        db_ok, db_err = check_db_health(app)
        predictor = get_predictor(app.config["MODEL_PATH"], app.config["MODEL_CONFIG_PATH"])
        ai_ok, ai_msg = predictor.is_ready()
        status_code = 200 if db_ok else 200
        return (
            jsonify(
                {
                    "status": "ok" if db_ok else "degraded",
                    "database": "connected" if db_ok else "unavailable",
                    "database_error": db_err,
                    "ai_model": "ready" if ai_ok else "unconfigured",
                    "ai_model_message": ai_msg or "Model and preprocessing configuration verified.",
                }
            ),
            status_code,
        )

    @app.errorhandler(413)
    def file_too_large(_err):
        max_mb = app.config["MAX_CONTENT_LENGTH"] / (1024 * 1024)
        return jsonify({"error": f"Uploaded file exceeds the {max_mb:.0f} MB limit."}), 413

    @app.errorhandler(429)
    def rate_limited(_err):
        return jsonify({"error": "Too many requests. Please wait a moment before trying again."}), 429

    @app.errorhandler(404)
    def not_found(_err):
        return jsonify({"error": "Requested resource was not found."}), 404

    socketio.init_app(
        app,
        cors_allowed_origins=app.config["CORS_ORIGINS"],
        async_mode="threading",
    )
    register_socket_handlers(socketio)

    # Auto-bootstrap default admin on first start (dev/demo convenience)
    _bootstrap_admin(app)

    return app


def _bootstrap_admin(app):
    """Create a default admin account if none exists (dev/demo mode only)."""
    import os

    admin_email = os.getenv("BOOTSTRAP_ADMIN_EMAIL", "admin@retinal.ai")
    admin_password = os.getenv("BOOTSTRAP_ADMIN_PASSWORD", "RetinalAdmin2024!")
    admin_name = os.getenv("BOOTSTRAP_ADMIN_NAME", "Platform Administrator")

    with app.app_context():
        from database.db import get_db
        from models.user_model import UserModel

        db = get_db()
        if db is None:
            return  # No DB connected yet — skip silently

        try:
            if not UserModel.find_by_email(admin_email):
                UserModel.create(
                    full_name=admin_name,
                    email=admin_email,
                    phone="+10000000000",
                    password=admin_password,
                    role="admin",
                    account_status="active",
                )
                app.logger.info(f"[Bootstrap] Admin account created: {admin_email}")
            else:
                app.logger.info(f"[Bootstrap] Admin already exists: {admin_email}")
        except Exception as exc:
            app.logger.warning(f"[Bootstrap] Admin creation skipped: {exc}")


if __name__ == "__main__":
    application = create_app()
    socketio.run(
        application,
        host="0.0.0.0",
        port=5000,
        debug=application.config["FLASK_DEBUG"],
        allow_unsafe_werkzeug=True,
    )
