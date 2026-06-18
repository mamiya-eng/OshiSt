from flask import Blueprint, flash, redirect, render_template, request, url_for

from config import Config
from oshist.dao import brand_dao, category_dao, character_dao, item_dao, series_dao, store_dao
from oshist.services.item_service import ItemService
from oshist.utils.auth import get_current_user_id, login_required
from oshist.utils.csrf import validate_csrf_token
from oshist.utils.image import delete_uploaded_image, save_uploaded_image
from oshist.utils.validators import DELIVERY_STATUS_LABELS, PURCHASE_ROUTE_LABELS

items_bp = Blueprint("items", __name__, url_prefix="/items")
item_service = ItemService()


@items_bp.route("/")
@login_required
def list_items():
    """アイテム一覧と検索結果を表示する。"""
    user_id = get_current_user_id()
    try:
        filters = item_service.parse_search_filters(user_id, request.args)
        items = item_dao.search(user_id, filters)
    except ValueError as exc:
        flash(str(exc), "error")
        filters = {"include_drafts": False}
        items = item_dao.list_by_user(user_id, include_drafts=False)

    return render_template(
        "items/list.html",
        items=items,
        filters=filters,
        series_list=series_dao.list_by_user(user_id),
        categories=category_dao.list_by_user(user_id),
        characters=character_dao.list_by_user(user_id),
        delivery_statuses=Config.DELIVERY_STATUSES,
        delivery_status_labels=DELIVERY_STATUS_LABELS,
        route_labels=PURCHASE_ROUTE_LABELS,
        route_label=item_service.purchase_route_label,
    )


@items_bp.route("/<int:item_id>")
@login_required
def detail(item_id: int):
    """アイテム詳細を表示する。"""
    user_id = get_current_user_id()
    item = item_dao.find_by_id(user_id, item_id)
    if not item:
        return ("Not Found", 404)
    return render_template(
        "items/detail.html",
        item=item,
        route_label=item_service.purchase_route_label(item.purchase_route_code),
        delivery_status_label=DELIVERY_STATUS_LABELS.get(
            item.delivery_status, item.delivery_status
        ),
    )


@items_bp.route("/new", methods=["GET", "POST"])
@login_required
def create():
    """アイテムを新規登録する。"""
    user_id = get_current_user_id()
    stores = store_dao.list_by_user(user_id)
    brands = brand_dao.list_by_user(user_id)
    series_list = series_dao.list_by_user(user_id)
    categories = category_dao.list_by_user(user_id)
    characters = character_dao.list_by_user(user_id)

    if request.method == "POST":
        if not validate_csrf_token(request.form.get("csrf_token")):
            return ("Forbidden", 403)
        try:
            data = item_service.parse_form(user_id, request.form, request.files)
            image_path = None
            image_file = data.pop("image_file", None)
            if image_file and image_file.filename:
                image_path = save_uploaded_image(image_file)

            try:
                item_id = item_service.create_item(user_id, data, image_path)
            except Exception:
                if image_path:
                    delete_uploaded_image(image_path)
                raise
            flash("アイテムを登録しました。", "success")
            return redirect(url_for("items.detail", item_id=item_id))
        except ValueError as exc:
            flash(str(exc), "error")

    return render_template(
        "items/form.html",
        item=None,
        selected_character_ids=[],
        stores=stores,
        brands=brands,
        series_list=series_list,
        categories=categories,
        characters=characters,
        delivery_statuses=Config.DELIVERY_STATUSES,
        delivery_status_labels=DELIVERY_STATUS_LABELS,
        route_codes=PURCHASE_ROUTE_LABELS,
        form_action=url_for("items.create"),
        cancel_url=url_for("items.list_items"),
        cancel_label="← 一覧に戻る",
    )


@items_bp.route("/<int:item_id>/edit", methods=["GET", "POST"])
@login_required
def edit(item_id: int):
    """アイテムを編集する。"""
    user_id = get_current_user_id()
    item = item_dao.find_by_id(user_id, item_id)
    if not item:
        return ("Not Found", 404)

    stores = store_dao.list_by_user(user_id)
    brands = brand_dao.list_by_user(user_id)
    series_list = series_dao.list_by_user(user_id)
    categories = category_dao.list_by_user(user_id)
    characters = character_dao.list_by_user(user_id)
    selected_character_ids = item_dao.list_character_ids(user_id, item_id)

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
        selected_character_ids=selected_character_ids,
        stores=stores,
        brands=brands,
        series_list=series_list,
        categories=categories,
        characters=characters,
        delivery_statuses=Config.DELIVERY_STATUSES,
        delivery_status_labels=DELIVERY_STATUS_LABELS,
        route_codes=PURCHASE_ROUTE_LABELS,
        form_action=url_for("items.edit", item_id=item_id),
        cancel_url=url_for("items.detail", item_id=item_id),
        cancel_label="← 戻る",
    )


@items_bp.route("/<int:item_id>/delete", methods=["POST"])
@login_required
def delete(item_id: int):
    """Delete a user-owned item."""
    if not validate_csrf_token(request.form.get("csrf_token")):
        return ("Forbidden", 403)

    user_id = get_current_user_id()
    if not item_service.delete_item(user_id, item_id):
        flash("削除対象のアイテムが見つかりません。", "error")
        return ("Not Found", 404)

    flash("アイテムを削除しました。", "success")
    return redirect(url_for("items.list_items"))
