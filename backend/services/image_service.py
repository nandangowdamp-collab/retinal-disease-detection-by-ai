from pathlib import Path
import uuid
from PIL import Image, UnidentifiedImageError
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}
ALLOWED_PIL_FORMATS = {"JPEG", "PNG"}


class ImageValidationError(ValueError):
    """Raised when an uploaded retinal image fails format, integrity, or size validation."""


def resolve_upload_path(upload_folder: str, stored_filename: str) -> Path:
    base = Path(upload_folder).resolve()
    target = (base / stored_filename).resolve()
    if base not in target.parents and target != base:
        raise ImageValidationError("Invalid image path.")
    return target


def validate_and_save_retinal_image(file_storage, upload_folder: str, max_bytes: int) -> tuple[str, str]:
    if file_storage is None or not file_storage.filename:
        raise ImageValidationError("No retinal image file provided.")

    original_name = secure_filename(file_storage.filename)
    if "." not in original_name:
        raise ImageValidationError("File must have a valid image extension (.jpg, .jpeg, .png).")

    ext = original_name.rsplit(".", 1)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ImageValidationError("Unsupported file type. Allowed formats: JPG, JPEG, PNG.")

    stream = file_storage.stream
    stream.seek(0, 2)
    size = stream.tell()
    stream.seek(0)
    if size <= 0:
        raise ImageValidationError("Uploaded image file is empty.")
    if size > max_bytes:
        max_mb = max_bytes / (1024 * 1024)
        raise ImageValidationError(f"Image exceeds maximum allowed size of {max_mb:.1f} MB.")

    try:
        img = Image.open(stream)
        img.verify()
    except (UnidentifiedImageError, OSError) as exc:
        raise ImageValidationError("Uploaded file is not a valid or readable image.") from exc

    stream.seek(0)
    try:
        with Image.open(stream) as verified_img:
            if verified_img.format not in ALLOWED_PIL_FORMATS:
                raise ImageValidationError("Image content must be JPEG or PNG.")
            if verified_img.width < 32 or verified_img.height < 32:
                raise ImageValidationError("Image dimensions must be at least 32x32 pixels.")
    except ImageValidationError:
        raise
    except Exception as exc:
        raise ImageValidationError("Could not decode uploaded retinal image.") from exc

    upload_dir = Path(upload_folder).resolve()
    upload_dir.mkdir(parents=True, exist_ok=True)
    stored_filename = f"{uuid.uuid4().hex}.{ext}"
    dest = resolve_upload_path(str(upload_dir), stored_filename)
    stream.seek(0)
    file_storage.save(str(dest))
    return stored_filename, original_name
