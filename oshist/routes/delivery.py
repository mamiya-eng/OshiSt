from flask import Blueprint, flash, redirect, render_template, request, url_for

from config import Config
from oshist.services.delivery_service import DeliveryService
from oshist.utils.auth import get_current_user_id, login_required
from oshist.utils.csrf import validate_csrf_token
from oshist.utils.validators import DELIVERY_STATUS_LABELS

delivery_bp = Blueprint("delivery", __name__, url_prefix="/delivery")
delivery_service = DeliveryService()


@delivery_bp.route("/")
@login_required
def index():
    """配送管理画面を表示する。"""
    user_id = get_current_user_id()
    status = (request.args.get("status") or "").strip() or None
    try:
        items = delivery_service.list_deliveries(user_id, status)
    except ValueError as exc:
        flash(str(exc), "error")
        return redirect(url_for("delivery.index"))

    return render_template(
        "delivery/index.html",
        items=items,
        selected_status=status,
        delivery_statuses=Config.DELIVERY_STATUSES,
        delivery_status_labels=DELIVERY_STATUS_LABELS,
    )


@delivery_bp.route("/<int:item_id>", methods=["POST"])
@login_required
def update(item_id: int):
    """配送情報を更新する。"""
    if not validate_csrf_token(request.form.get("csrf_token")):
        return ("Forbidden", 403)
    user_id = get_current_user_id()
    try:
        data = delivery_service.parse_update_form(request.form)
        if delivery_service.update_delivery(user_id, item_id, data):
            flash("配送情報を更新しました。", "success")
        else:
            flash("更新対象が見つかりません。", "error")
    except ValueError as exc:
        flash(str(exc), "error")
    return redirect(url_for("delivery.index", status=request.args.get("status", "")))
