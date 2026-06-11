import re
from pathlib import Path

from flask import Blueprint, abort, send_file

from config import Config
from oshist.dao import item_dao
from oshist.utils.auth import get_current_user_id, login_required

images_bp = Blueprint("images", __name__)

UUID_FILENAME_PATTERN = re.compile(
    r"^[0-9a-f]{32}\.(jpg|jpeg|png|webp)$", re.IGNORECASE
)


@images_bp.route("/images/<path:filename>")
@login_required
def serve_image(filename: str):
    if not UUID_FILENAME_PATTERN.match(filename):
        abort(404)

    item = item_dao.find_by_image_path(filename)
    if not item:
        abort(404)

    user_id = get_current_user_id()
    if item.user_id != user_id:
        abort(403)

    file_path = Path(Config.UPLOAD_DIR) / filename
    if not file_path.is_file():
        abort(404)

    return send_file(file_path)
