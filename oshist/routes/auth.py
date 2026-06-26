from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from oshist.services.auth_service import AuthService
from oshist.utils.csrf import validate_csrf_token

auth_bp = Blueprint("auth", __name__)
auth_service = AuthService()

"""ログイン画面の表示・処理"""
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if not validate_csrf_token(request.form.get("csrf_token")):  # CSRFトークン確認
            return ("Forbidden", 403)

        """入力内容を受け取りserviceへ渡す"""
        name = request.form.get("name", "")
        password = request.form.get("password", "")
        user = auth_service.authenticate(name, password)
        if not user:
            flash("ユーザー名またはパスワードが正しくありません。", "error")
            return render_template("login.html")

         #セッション固定攻撃を防ぐため、ログイン成功時に既存セッションを破棄する
        session.clear()
        session.permanent = True
        session["user_id"] = user.id
        session["user_name"] = user.name
        return redirect(url_for("home.index"))

    if "user_id" in session:
        return redirect(url_for("home.index"))
    return render_template("login.html")

"""新規登録画面の表示・処理"""
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        if not validate_csrf_token(request.form.get("csrf_token")):  # CSRFトークン確認
            return ("Forbidden", 403)

        try:
            auth_service.register(
                request.form.get("name", ""),
                request.form.get("password", ""),
            )
            flash("登録が完了しました。ログインしてください。", "success")
            return redirect(url_for("auth.login"))
        except ValueError as exc:
            flash(str(exc), "error")

    return render_template("register.html")

"""ログアウト画面の表示・処理"""
@auth_bp.route("/logout", methods=["POST"])
def logout():
    if not validate_csrf_token(request.form.get("csrf_token")):  # CSRFトークン確認
        return ("Forbidden", 403)
    session.clear()
    return redirect(url_for("auth.login"))
