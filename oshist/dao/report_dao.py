from decimal import Decimal

from oshist.db import get_connection


def list_purchase_years(user_id: int) -> list[int]:
    """正式登録済みアイテムの購入日からユーザー所有の年一覧を取得する。"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT DISTINCT YEAR(purchase_date) AS purchase_year
            FROM items
            WHERE user_id = %s
              AND draft_flg = FALSE
              AND purchase_date IS NOT NULL
            ORDER BY purchase_year DESC
            """,
            (user_id,),
        )
        return [int(row[0]) for row in cursor.fetchall()]


def monthly_spending(user_id: int, year: int) -> list[dict]:
    """対象年の月別使用額を取得する。"""
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT
                MONTH(purchase_date) AS month,
                SUM(price * quantity) AS amount
            FROM items
            WHERE user_id = %s
              AND draft_flg = FALSE
              AND price IS NOT NULL
              AND purchase_date IS NOT NULL
              AND YEAR(purchase_date) = %s
            GROUP BY MONTH(purchase_date)
            ORDER BY month
            """,
            (user_id, year),
        )
        return cursor.fetchall()


def series_spending(user_id: int, year: int, limit: int = 10) -> list[dict]:
    """対象年のシリーズ別使用額を上位順で取得する。"""
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT
                COALESCE(s.name, '未設定') AS label,
                SUM(i.price * i.quantity) AS amount
            FROM items i
            LEFT JOIN series s
              ON s.id = i.series_id
             AND s.user_id = i.user_id
            WHERE i.user_id = %s
              AND i.draft_flg = FALSE
              AND i.price IS NOT NULL
              AND i.purchase_date IS NOT NULL
              AND YEAR(i.purchase_date) = %s
            GROUP BY i.series_id, s.name
            HAVING SUM(i.price * i.quantity) > 0
            ORDER BY amount DESC, label
            LIMIT %s
            """,
            (user_id, year, limit),
        )
        return cursor.fetchall()


def category_spending(user_id: int, year: int, limit: int = 10) -> list[dict]:
    """対象年のカテゴリ別使用額を上位順で取得する。"""
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT
                COALESCE(c.name, '未設定') AS label,
                SUM(i.price * i.quantity) AS amount
            FROM items i
            LEFT JOIN categories c
              ON c.id = i.category_id
             AND c.user_id = i.user_id
            WHERE i.user_id = %s
              AND i.draft_flg = FALSE
              AND i.price IS NOT NULL
              AND i.purchase_date IS NOT NULL
              AND YEAR(i.purchase_date) = %s
            GROUP BY i.category_id, c.name
            HAVING SUM(i.price * i.quantity) > 0
            ORDER BY amount DESC, label
            LIMIT %s
            """,
            (user_id, year, limit),
        )
        return cursor.fetchall()


def decimal_amount(value) -> Decimal:
    """DB集計値をDecimalへ揃える。"""
    return Decimal(str(value or 0))
