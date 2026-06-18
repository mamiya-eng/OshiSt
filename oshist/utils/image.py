import imghdr
import logging
import uuid
from pathlib import Path

from config import Config

ALLOWED_IMAGE_TYPES = {"jpeg", "png", "webp"}
logger = logging.getLogger(__name__)


def detect_image_type(data: bytes) -> str | None:
    kind = imghdr.what(None, h=data)
    if kind == "jpeg":
        return "jpeg"
    if kind == "png":
        return "png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    return None


def save_uploaded_image(file_storage) -> str:
    data = file_storage.read()
    if len(data) > Config.MAX_UPLOAD_BYTES:
        raise ValueError("ファイルサイズが上限を超えています。")

    image_type = detect_image_type(data)
    if image_type not in ALLOWED_IMAGE_TYPES:
        raise ValueError("JPEG / PNG / WEBP のみアップロードできます。")

    ext_map = {"jpeg": ".jpg", "png": ".png", "webp": ".webp"}
    filename = f"{uuid.uuid4().hex}{ext_map[image_type]}"
    Config.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    path = Config.UPLOAD_DIR / filename
    path.write_bytes(data)
    return filename


def resolve_upload_path(filename: str | None) -> Path | None:
    """Return a safe upload path only when it stays inside UPLOAD_DIR."""
    if not filename:
        return None
    raw_path = Path(filename)
    if raw_path.is_absolute():
        return None

    upload_dir = Config.UPLOAD_DIR.resolve()
    candidate = (upload_dir / raw_path).resolve()
    try:
        candidate.relative_to(upload_dir)
    except ValueError:
        return None
    return candidate


def delete_uploaded_image(filename: str | None) -> bool:
    """Delete an uploaded image after checking it is inside UPLOAD_DIR."""
    path = resolve_upload_path(filename)
    if path is None:
        logger.warning("Skipped unsafe image delete target: %s", filename)
        return False
    if not path.exists():
        return True
    if not path.is_file():
        logger.warning("Skipped non-file image delete target: %s", path)
        return False
    try:
        path.unlink()
        return True
    except OSError:
        logger.exception("Failed to delete uploaded image: %s", path)
        return False
