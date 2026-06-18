from oshist.db import get_connection


def list_by_user(user_id: int) -> list[dict]:
    """ログインユーザーが登録したシリーズを一覧取得する。"""
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT
                s.id,
                s.name,
                s.description,
                COUNT(DISTINCT i.id) AS item_count,
                COUNT(DISTINCT ch.id) AS character_count
            FROM series s
            LEFT JOIN items i
              ON i.series_id = s.id
             AND i.user_id = s.user_id
            LEFT JOIN characters ch
              ON ch.series_id = s.id
             AND ch.user_id = s.user_id
            WHERE s.user_id = %s
            GROUP BY s.id, s.name, s.description
            ORDER BY s.name
            """,
            (user_id,),
        )
        return cursor.fetchall()


def find_by_id(user_id: int, series_id: int) -> dict | None:
    """ユーザー所有のシリーズをIDで取得する。"""
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, name, description FROM series WHERE id = %s AND user_id = %s",
            (series_id, user_id),
        )
        return cursor.fetchone()


def find_by_name(
    user_id: int, name: str, exclude_series_id: int | None = None
) -> dict | None:
    """同一ユーザー内のシリーズ名重複を確認する。"""
    sql = "SELECT id, name FROM series WHERE user_id = %s AND name = %s"
    params: list = [user_id, name]
    if exclude_series_id:
        sql += " AND id <> %s"
        params.append(exclude_series_id)

    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql, tuple(params))
        return cursor.fetchone()


def count_items(user_id: int, series_id: int) -> int:
    """シリーズに紐づくアイテム数を取得する。"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM items WHERE user_id = %s AND series_id = %s",
            (user_id, series_id),
        )
        return cursor.fetchone()[0]


def count_characters(user_id: int, series_id: int) -> int:
    """シリーズに紐づくキャラ数を取得する。"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM characters WHERE user_id = %s AND series_id = %s",
            (user_id, series_id),
        )
        return cursor.fetchone()[0]


def create(user_id: int, name: str, description: str | None = None) -> int:
    """シリーズを登録する。"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO series (user_id, name, description) VALUES (%s, %s, %s)",
            (user_id, name, description),
        )
        return cursor.lastrowid


def update(
    user_id: int, series_id: int, name: str, description: str | None = None
) -> bool:
    """ユーザー所有のシリーズを更新する。"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE series
               SET name = %s, description = %s
             WHERE id = %s AND user_id = %s
            """,
            (name, description, series_id, user_id),
        )
        return cursor.rowcount > 0


def delete(user_id: int, series_id: int) -> bool:
    """ユーザー所有のシリーズを削除する。"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM series WHERE id = %s AND user_id = %s",
            (series_id, user_id),
        )
        return cursor.rowcount > 0
