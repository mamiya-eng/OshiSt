from flask import Blueprint, flash, redirect, render_template, request, url_for

from oshist.dao import category_dao, character_dao, series_dao
from oshist.services.master_service import MasterService
from oshist.utils.auth import get_current_user_id, login_required
from oshist.utils.csrf import validate_csrf_token

masters_bp = Blueprint("masters", __name__, url_prefix="/masters")
master_service = MasterService()


@masters_bp.route("/series", methods=["GET", "POST"])
@login_required
def series_index():
    """シリーズ一覧、登録、編集を行う。"""
    user_id = get_current_user_id()
    edit_id = request.args.get("edit_id", type=int)
    editing = series_dao.find_by_id(user_id, edit_id) if edit_id else None

    if request.method == "POST":
        if not validate_csrf_token(request.form.get("csrf_token")):
            return ("Forbidden", 403)
        try:
            data = master_service.parse_series_form(request.form)
            series_id = request.form.get("series_id", type=int)
            if series_id:
                master_service.update_series(user_id, series_id, data)
                flash("シリーズを更新しました。", "success")
            else:
                master_service.create_series(user_id, data)
                flash("シリーズを登録しました。", "success")
            return redirect(url_for("masters.series_index"))
        except ValueError as exc:
            flash(str(exc), "error")

    return render_template(
        "masters/series.html",
        series_list=series_dao.list_by_user(user_id),
        editing=editing,
    )


@masters_bp.route("/series/<int:series_id>/delete", methods=["POST"])
@login_required
def delete_series(series_id: int):
    """未使用のシリーズを削除する。"""
    if not validate_csrf_token(request.form.get("csrf_token")):
        return ("Forbidden", 403)
    user_id = get_current_user_id()
    try:
        master_service.delete_series(user_id, series_id)
        flash("シリーズを削除しました。", "success")
    except ValueError as exc:
        flash(str(exc), "error")
    return redirect(url_for("masters.series_index"))


@masters_bp.route("/categories", methods=["GET", "POST"])
@login_required
def categories_index():
    """カテゴリ一覧、登録、編集を行う。"""
    user_id = get_current_user_id()
    edit_id = request.args.get("edit_id", type=int)
    editing = category_dao.find_by_id(user_id, edit_id) if edit_id else None

    if request.method == "POST":
        if not validate_csrf_token(request.form.get("csrf_token")):
            return ("Forbidden", 403)
        try:
            data = master_service.parse_category_form(request.form)
            category_id = request.form.get("category_id", type=int)
            if category_id:
                master_service.update_category(user_id, category_id, data)
                flash("カテゴリを更新しました。", "success")
            else:
                master_service.create_category(user_id, data)
                flash("カテゴリを登録しました。", "success")
            return redirect(url_for("masters.categories_index"))
        except ValueError as exc:
            flash(str(exc), "error")

    return render_template(
        "masters/categories.html",
        categories=category_dao.list_by_user(user_id),
        editing=editing,
    )


@masters_bp.route("/categories/<int:category_id>/delete", methods=["POST"])
@login_required
def delete_category(category_id: int):
    """未使用のカテゴリを削除する。"""
    if not validate_csrf_token(request.form.get("csrf_token")):
        return ("Forbidden", 403)
    user_id = get_current_user_id()
    try:
        master_service.delete_category(user_id, category_id)
        flash("カテゴリを削除しました。", "success")
    except ValueError as exc:
        flash(str(exc), "error")
    return redirect(url_for("masters.categories_index"))


@masters_bp.route("/characters", methods=["GET", "POST"])
@login_required
def characters_index():
    """キャラ一覧、登録、編集を行う。"""
    user_id = get_current_user_id()
    edit_id = request.args.get("edit_id", type=int)
    editing = character_dao.find_by_id(user_id, edit_id) if edit_id else None
    series_list = series_dao.list_by_user(user_id)

    if request.method == "POST":
        if not validate_csrf_token(request.form.get("csrf_token")):
            return ("Forbidden", 403)
        try:
            data = master_service.parse_character_form(user_id, request.form)
            character_id = request.form.get("character_id", type=int)
            if character_id:
                master_service.update_character(user_id, character_id, data)
                flash("キャラを更新しました。", "success")
            else:
                master_service.create_character(user_id, data)
                flash("キャラを登録しました。", "success")
            return redirect(url_for("masters.characters_index"))
        except ValueError as exc:
            flash(str(exc), "error")

    return render_template(
        "masters/characters.html",
        characters=character_dao.list_by_user(user_id),
        series_list=series_list,
        editing=editing,
    )


@masters_bp.route("/characters/<int:character_id>/delete", methods=["POST"])
@login_required
def delete_character(character_id: int):
    """未使用のキャラを削除する。"""
    if not validate_csrf_token(request.form.get("csrf_token")):
        return ("Forbidden", 403)
    user_id = get_current_user_id()
    try:
        master_service.delete_character(user_id, character_id)
        flash("キャラを削除しました。", "success")
    except ValueError as exc:
        flash(str(exc), "error")
    return redirect(url_for("masters.characters_index"))
