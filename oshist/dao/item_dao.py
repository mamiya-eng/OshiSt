from datetime import date, datetime
from decimal import Decimal

from oshist.db import get_connection
from oshist.models import Item

_ITEM_SELECT = """
    SELECT
        i.id, i.user_id, i.series_id, i.category_id, i.name,
        i.purchase_date, i.price, i.quantity, i.memo, i.image_path,
        i.barcode, i.store_id, i.brand_id, i.purchase_route_code,
        i.purchase_url, i.favorite, i.expected_delivery_date,
        i.delivery_status, i.delivery_reminder_enabled, i.draft_flg,
        i.created_at, i.updated_at,
        s.name AS series_name,
        c.name AS category_name,
        st.name AS store_name
    FROM items i
    LEFT JOIN series s ON i.series_id = s.id
    LEFT JOIN categories c ON i.category_id = c.id
    LEFT JOIN stores st ON i.store_id = st.id
"""


def _row_to_item(row: dict) -> Item:
    return Item(**row)


def find_by_id(user_id: int, item_id: int) -> Item | None:
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            _ITEM_SELECT + " WHERE i.id = %s AND i.user_id = %s",
            (item_id, user_id),
        )
        row = cursor.fetchone()
        return _row_to_item(row) if row else None


def find_by_image_path(image_path: str) -> Item | None:
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            _ITEM_SELECT + " WHERE i.image_path = %s",
            (image_path,),
        )
        row = cursor.fetchone()
        return _row_to_item(row) if row else None


def list_by_user(user_id: int, include_drafts: bool = True) -> list[Item]:
    sql = _ITEM_SELECT + " WHERE i.user_id = %s"
    params: list = [user_id]
    if not include_drafts:
        sql += " AND i.draft_flg = FALSE"
    sql += " ORDER BY i.updated_at DESC"

    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql, tuple(params))
        return [_row_to_item(row) for row in cursor.fetchall()]


def list_recent(user_id: int, limit: int = 5) -> list[Item]:
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            _ITEM_SELECT
            + " WHERE i.user_id = %s ORDER BY i.created_at DESC LIMIT %s",
            (user_id, limit),
        )
        return [_row_to_item(row) for row in cursor.fetchall()]


def count_all(user_id: int) -> int:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM items WHERE user_id = %s AND draft_flg = FALSE",
            (user_id,),
        )
        return cursor.fetchone()[0]


def create(
    user_id: int,
    name: str,
    quantity: int,
    draft_flg: bool,
    purchase_date: date | None = None,
    price: Decimal | None = None,
    purchase_route_code: str | None = None,
    purchase_url: str | None = None,
    store_id: int | None = None,
    memo: str | None = None,
    image_path: str | None = None,
    delivery_status: str = "delivered",
) -> int:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO items (
                user_id, name, quantity, draft_flg, purchase_date, price,
                purchase_route_code, purchase_url, store_id, memo, image_path,
                delivery_status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                user_id,
                name,
                quantity,
                draft_flg,
                purchase_date,
                price,
                purchase_route_code,
                purchase_url,
                store_id,
                memo,
                image_path,
                delivery_status,
            ),
        )
        return cursor.lastrowid


def update(
    user_id: int,
    item_id: int,
    name: str,
    quantity: int,
    draft_flg: bool,
    purchase_date: date | None = None,
    price: Decimal | None = None,
    purchase_route_code: str | None = None,
    purchase_url: str | None = None,
    store_id: int | None = None,
    memo: str | None = None,
    image_path: str | None = None,
    delivery_status: str = "delivered",
) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE items SET
                name = %s, quantity = %s, draft_flg = %s,
                purchase_date = %s, price = %s,
                purchase_route_code = %s, purchase_url = %s,
                store_id = %s, memo = %s, image_path = %s,
                delivery_status = %s, updated_at = %s
            WHERE id = %s AND user_id = %s
            """,
            (
                name,
                quantity,
                draft_flg,
                purchase_date,
                price,
                purchase_route_code,
                purchase_url,
                store_id,
                memo,
                image_path,
                delivery_status,
                datetime.now(),
                item_id,
                user_id,
            ),
        )
        return cursor.rowcount > 0


def sum_spending_for_month(user_id: int, year: int, month: int) -> Decimal:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT COALESCE(SUM(COALESCE(price, 0) * quantity), 0)
            FROM items
            WHERE user_id = %s
              AND draft_flg = FALSE
              AND delivery_status <> 'cancelled'
              AND purchase_date IS NOT NULL
              AND YEAR(purchase_date) = %s
              AND MONTH(purchase_date) = %s
            """,
            (user_id, year, month),
        )
        return Decimal(str(cursor.fetchone()[0]))
