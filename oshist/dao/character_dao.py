from oshist.db import get_connection


def list_by_user(user_id: int) -> list[dict]:
    """ログインユーザーが登録したキャラを一覧取得する。"""
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT
                ch.id,
                ch.series_id,
                ch.name,
                ch.color,
                s.name AS series_name,
                COUNT(DISTINCT i.id) AS item_count
            FROM characters ch
            INNER JOIN series s
              ON ch.series_id = s.id
             AND ch.user_id = s.user_id
            LEFT JOIN item_characters ic
              ON ic.character_id = ch.id
            LEFT JOIN items i
              ON i.id = ic.item_id
             AND i.user_id = ch.user_id
            WHERE ch.user_id = %s
            GROUP BY ch.id, ch.series_id, ch.name, ch.color, s.name
            ORDER BY s.name, ch.name
            """,
            (user_id,),
        )
        return cursor.fetchall()


def find_by_id(user_id: int, character_id: int) -> dict | None:
    """ユーザー所有のキャラをIDで取得する。"""
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, series_id, name, color
            FROM characters
            WHERE id = %s AND user_id = %s
            """,
            (character_id, user_id),
        )
        return cursor.fetchone()


def find_by_name(
    user_id: int,
    series_id: int,
    name: str,
    exclude_character_id: int | None = None,
) -> dict | None:
    """同一ユーザー・同一シリーズ内のキャラ名重複を確認する。"""
    sql = """
        SELECT id, name
        FROM characters
        WHERE user_id = %s AND series_id = %s AND name = %s
    """
    params: list = [user_id, series_id, name]
    if exclude_character_id:
        sql += " AND id <> %s"
        params.append(exclude_character_id)

    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql, tuple(params))
        return cursor.fetchone()


def count_items(user_id: int, character_id: int) -> int:
    """キャラに紐づくユーザー所有アイテム数を取得する。"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT COUNT(DISTINCT i.id)
            FROM item_characters ic
            INNER JOIN items i ON i.id = ic.item_id
            WHERE i.user_id = %s AND ic.character_id = %s
            """,
            (user_id, character_id),
        )
        return cursor.fetchone()[0]


def create(user_id: int, name: str, series_id: int, color: str | None = None) -> int:
    """キャラを登録する。"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO characters (user_id, series_id, name, color)
            VALUES (%s, %s, %s, %s)
            """,
            (user_id, series_id, name, color),
        )
        return cursor.lastrowid


def update(
    user_id: int,
    character_id: int,
    name: str,
    series_id: int,
    color: str | None = None,
) -> bool:
    """ユーザー所有のキャラを更新する。"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE characters
               SET name = %s, series_id = %s, color = %s
             WHERE id = %s AND user_id = %s
            """,
            (name, series_id, color, character_id, user_id),
        )
        return cursor.rowcount > 0


def delete(user_id: int, character_id: int) -> bool:
    """ユーザー所有のキャラを削除する。"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM characters WHERE id = %s AND user_id = %s",
            (character_id, user_id),
        )
        return cursor.rowcount > 0
