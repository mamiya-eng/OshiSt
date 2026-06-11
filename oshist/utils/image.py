import imghdr
import uuid
from pathlib import Path

from config import Config

ALLOWED_IMAGE_TYPES = {"jpeg", "png", "webp"}


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
    path = Config.UPLOAD_DIR / filename
    path.write_bytes(data)
    return filename
