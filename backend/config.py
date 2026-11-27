import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def _resolve_path(raw_path: str, default_rel: str) -> str:
    value = raw_path or default_rel
    p = Path(value)
    if not p.is_absolute():
        p = BASE_DIR / p
    return str(p.resolve())


def _parse_origins(raw_origins: str, debug: bool) -> list[str]:
    origins = [o.strip().rstrip("/") for o in (raw_origins or "").split(",") if o.strip()]
    if debug:
        for local_origin in ("http://localhost:5173", "http://127.0.0.1:5173"):
            if local_origin not in origins:
                origins.append(local_origin)
    return origins or ["http://localhost:5173"]


class Config:
    FLASK_DEBUG = os.getenv("FLASK_DEBUG", "false").lower() in ("1", "true", "yes")
    SECRET_KEY = os.getenv("SECRET_KEY") or os.urandom(32).hex()
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY") or os.urandom(32).hex()
    JWT_ACCESS_TOKEN_EXPIRES_HOURS = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_HOURS", "24"))

    MONGO_URI = os.getenv("MONGO_URI", "").strip()
    DATABASE_NAME = os.getenv("DATABASE_NAME", "retinal_ai_db").strip() or "retinal_ai_db"

    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
    CORS_ORIGINS = _parse_origins(FRONTEND_URL, FLASK_DEBUG)

    RATE_LIMIT_STORAGE_URI = os.getenv("RATE_LIMIT_STORAGE_URI", "memory://").strip() or "memory://"

    UPLOAD_FOLDER = _resolve_path(os.getenv("UPLOAD_FOLDER", ""), "uploads")
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", str(10 * 1024 * 1024)))
    ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}

    MODEL_PATH = _resolve_path(os.getenv("MODEL_PATH", ""), "ai_model/retinal_model.keras")
    MODEL_CONFIG_PATH = _resolve_path(os.getenv("MODEL_CONFIG_PATH", ""), "ai_model/preprocessing.json")

    TESTING = False
