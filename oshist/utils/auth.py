from functools import wraps

from flask import abort, redirect, session, url_for


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)

    return wrapped


def get_current_user_id() -> int:
    user_id = session.get("user_id")
    if user_id is None:
        abort(403)
    return int(user_id)
