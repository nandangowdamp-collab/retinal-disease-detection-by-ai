import re

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
PHONE_RE = re.compile(r"^[0-9+\-\s()]{7,20}$")


def sanitize_text(value, max_len: int = 1000) -> str:
    if value is None:
        return ""
    return str(value).strip()[:max_len]


def validate_email(email: str) -> bool:
    return bool(email and EMAIL_RE.match(email.strip()))


def validate_phone(phone: str) -> bool:
    return bool(phone and PHONE_RE.match(phone.strip()))


def validate_password(password: str, min_length: int = 8) -> tuple[bool, str | None]:
    if not password or len(password) < min_length:
        return False, f"Password must be at least {min_length} characters long."
    if not any(ch.isalpha() for ch in password) or not any(ch.isdigit() for ch in password):
        return False, "Password must contain at least one letter and one number."
    return True, None


def validate_required_fields(data: dict, required_fields: list[str]) -> list[str]:
    missing = []
    for field in required_fields:
        val = data.get(field)
        if val is None or (isinstance(val, str) and not val.strip()):
            missing.append(field)
    return missing


def validate_positive_int(value, min_val: int = 0, max_val: int = 150) -> int | None:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    if parsed < min_val or parsed > max_val:
        return None
    return parsed
