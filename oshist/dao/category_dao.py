from oshist.db import get_connection


def list_by_user(user_id: int) -> list[dict]:
    """ログインユーザーが登録したカテゴリを一覧取得する。"""
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT
                c.id,
                c.name,
                COUNT(i.id) AS item_count
            FROM categories c
            LEFT JOIN items i
              ON i.category_id = c.id
             AND i.user_id = c.user_id
            WHERE c.user_id = %s
            GROUP BY c.id, c.name
            ORDER BY c.name
            """,
            (user_id,),
        )
        return cursor.fetchall()


def find_by_id(user_id: int, category_id: int) -> dict | None:
    """ユーザー所有のカテゴリをIDで取得する。"""
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, name FROM categories WHERE id = %s AND user_id = %s",
            (category_id, user_id),
        )
        return cursor.fetchone()


def find_by_name(
    user_id: int, name: str, exclude_category_id: int | None = None
) -> dict | None:
    """同一ユーザー内のカテゴリ名重複を確認する。"""
    sql = "SELECT id, name FROM categories WHERE user_id = %s AND name = %s"
    params: list = [user_id, name]
    if exclude_category_id:
        sql += " AND id <> %s"
        params.append(exclude_category_id)

    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql, tuple(params))
        return cursor.fetchone()


def count_items(user_id: int, category_id: int) -> int:
    """カテゴリに紐づくアイテム数を取得する。"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM items WHERE user_id = %s AND category_id = %s",
            (user_id, category_id),
        )
        return cursor.fetchone()[0]


def create(user_id: int, name: str) -> int:
    """カテゴリを登録する。"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO categories (user_id, name) VALUES (%s, %s)",
            (user_id, name),
        )
        return cursor.lastrowid


def update(user_id: int, category_id: int, name: str) -> bool:
    """ユーザー所有のカテゴリを更新する。"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE categories SET name = %s WHERE id = %s AND user_id = %s",
            (name, category_id, user_id),
        )
        return cursor.rowcount > 0


def delete(user_id: int, category_id: int) -> bool:
    """ユーザー所有のカテゴリを削除する。"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM categories WHERE id = %s AND user_id = %s",
            (category_id, user_id),
        )
        return cursor.rowcount > 0
