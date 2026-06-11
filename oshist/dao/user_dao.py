from oshist.db import get_connection
from oshist.models import User


def find_by_name(name: str) -> User | None:
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, name, password_hash, theme_type, accent_color FROM users WHERE name = %s",
            (name,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return User(**row)


def find_by_id(user_id: int) -> User | None:
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, name, password_hash, theme_type, accent_color FROM users WHERE id = %s",
            (user_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return User(**row)


def create(name: str, password_hash: str) -> int:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (name, password_hash) VALUES (%s, %s)",
            (name, password_hash),
        )
        return cursor.lastrowid
