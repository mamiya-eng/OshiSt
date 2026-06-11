import secrets

from flask import session


def generate_csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(32)
    return session["csrf_token"]


def validate_csrf_token(token: str | None) -> bool:
    if not token:
        return False
    expected = session.get("csrf_token")
    return bool(expected) and secrets.compare_digest(expected, token)
