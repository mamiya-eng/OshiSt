from flask import Blueprint, flash, redirect, render_template, request, url_for

from oshist.dao import item_dao, store_dao
from oshist.services.item_service import ItemService
from oshist.utils.auth import get_current_user_id, login_required
from oshist.utils.csrf import validate_csrf_token
from oshist.utils.image import save_uploaded_image
from oshist.utils.validators import PURCHASE_ROUTE_LABELS

items_bp = Blueprint("items", __name__, url_prefix="/items")
item_service = ItemService()


@items_bp.route("/")
@login_required
def list_items():
    user_id = get_current_user_id()
    items = item_dao.list_by_user(user_id)
    return render_template(
        "items/list.html",
        items=items,
        route_labels=PURCHASE_ROUTE_LABELS,
        route_label=item_service.purchase_route_label,
    )


@items_bp.route("/<int:item_id>")
@login_required
def detail(item_id: int):
    user_id = get_current_user_id()
    item = item_dao.find_by_id(user_id, item_id)
    if not item:
        return ("Not Found", 404)
    return render_template(
        "items/detail.html",
        item=item,
        route_label=item_service.purchase_route_label(item.purchase_route_code),
    )


@items_bp.route("/new", methods=["GET", "POST"])
@login_required
def create():
    user_id = get_current_user_id()
    stores = store_dao.list_by_user(user_id)

    if request.method == "POST":
        if not validate_csrf_token(request.form.get("csrf_token")):
            return ("Forbidden", 403)
        try:
            data = item_service.parse_form(user_id, request.form, request.files)
            image_path = None
            image_file = data.pop("image_file", None)
            if image_file and image_file.filename:
                image_path = save_uploaded_image(image_file)

            item_id = item_service.create_item(user_id, data, image_path)
            flash("アイテムを登録しました。", "success")
            return redirect(url_for("items.detail", item_id=item_id))
        except ValueError as exc:
            flash(str(exc), "error")

    return render_template(
        "items/form.html",
        item=None,
        stores=stores,
        route_codes=PURCHASE_ROUTE_LABELS,
        form_action=url_for("items.create"),
    )


@items_bp.route("/<int:item_id>/edit", methods=["GET", "POST"])
@login_required
def edit(item_id: int):
    user_id = get_current_user_id()
    item = item_dao.find_by_id(user_id, item_id)
    if not item:
        return ("Not Found", 404)

    stores = store_dao.list_by_user(user_id)

    if request.method == "POST":
        if not validate_csrf_token(request.form.get("csrf_token")):
            return ("Forbidden", 403)
        try:
            data = item_service.parse_form(user_id, request.form, request.files)
            image_path = None
            image_file = data.pop("image_file", None)
            if image_file and image_file.filename:
                image_path = save_uploaded_image(image_file)

            if item_service.update_item(user_id, item_id, data, image_path):
                flash("アイテムを更新しました。", "success")
                return redirect(url_for("items.detail", item_id=item_id))
            flash("更新に失敗しました。", "error")
        except ValueError as exc:
            flash(str(exc), "error")

    return render_template(
        "items/form.html",
        item=item,
        stores=stores,
        route_codes=PURCHASE_ROUTE_LABELS,
        form_action=url_for("items.edit", item_id=item_id),
    )
