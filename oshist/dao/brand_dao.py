from oshist.db import get_connection


def list_by_user(user_id: int) -> list[dict]:
    """Return brands owned by the user."""
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, name
            FROM brands
            WHERE user_id = %s
              AND name IS NOT NULL
              AND TRIM(name) <> ''
            ORDER BY name
            """,
            (user_id,),
        )
        return cursor.fetchall()


def find_or_create(user_id: int, name: str) -> int:
    """Find an owned brand by name, or create it."""
    name = name.strip()
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id FROM brands WHERE user_id = %s AND name = %s",
            (user_id, name),
        )
        row = cursor.fetchone()
        if row:
            return row["id"]
        cursor.execute(
            "INSERT INTO brands (user_id, name) VALUES (%s, %s)",
            (user_id, name),
        )
        return cursor.lastrowid
