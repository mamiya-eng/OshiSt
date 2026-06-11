from oshist.db import get_connection


def list_by_user(user_id: int) -> list[dict]:
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, name FROM stores WHERE user_id = %s ORDER BY name",
            (user_id,),
        )
        return cursor.fetchall()


def find_or_create(user_id: int, name: str) -> int:
    name = name.strip()
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id FROM stores WHERE user_id = %s AND name = %s",
            (user_id, name),
        )
        row = cursor.fetchone()
        if row:
            return row["id"]
        cursor.execute(
            "INSERT INTO stores (user_id, name) VALUES (%s, %s)",
            (user_id, name),
        )
        return cursor.lastrowid
