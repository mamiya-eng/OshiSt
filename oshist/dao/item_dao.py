from datetime import date, datetime
from decimal import Decimal

from oshist.db import get_connection
from oshist.models import Item

_ITEM_SELECT = """
    SELECT
        i.id, i.user_id, i.series_id, i.category_id, i.name,
        i.purchase_date, i.price, i.quantity, i.memo, i.image_path,
        i.store_id, i.brand_id, i.purchase_route_code,
        i.purchase_url, i.favorite, i.expected_delivery_date,
        i.delivery_status, i.delivery_reminder_enabled, i.draft_flg,
        i.created_at, i.updated_at,
        s.name AS series_name,
        c.name AS category_name,
        st.name AS store_name,
        b.name AS brand_name,
        GROUP_CONCAT(DISTINCT ch.name ORDER BY ch.name SEPARATOR ', ') AS character_names
    FROM items i
    LEFT JOIN series s
      ON i.series_id = s.id
     AND i.user_id = s.user_id
    LEFT JOIN categories c
      ON i.category_id = c.id
     AND i.user_id = c.user_id
    LEFT JOIN stores st
      ON i.store_id = st.id
     AND i.user_id = st.user_id
    LEFT JOIN brands b
      ON i.brand_id = b.id
     AND i.user_id = b.user_id
    LEFT JOIN item_characters ic ON i.id = ic.item_id
    LEFT JOIN characters ch
      ON ic.character_id = ch.id
     AND i.user_id = ch.user_id
"""

_ITEM_GROUP_BY = """
    GROUP BY
        i.id, i.user_id, i.series_id, i.category_id, i.name,
        i.purchase_date, i.price, i.quantity, i.memo, i.image_path,
        i.store_id, i.brand_id, i.purchase_route_code,
        i.purchase_url, i.favorite, i.expected_delivery_date,
        i.delivery_status, i.delivery_reminder_enabled, i.draft_flg,
        i.created_at, i.updated_at,
        s.name, c.name, st.name, b.name
"""


def _row_to_item(row: dict) -> Item:
    """DB行をItemデータクラスへ変換する。"""
    return Item(**row)


def find_by_id(user_id: int, item_id: int) -> Item | None:
    """ユーザー所有のアイテムをIDで取得する。"""
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            _ITEM_SELECT + " WHERE i.id = %s AND i.user_id = %s" + _ITEM_GROUP_BY,
            (item_id, user_id),
        )
        row = cursor.fetchone()
        return _row_to_item(row) if row else None


def find_by_image_path(user_id: int, image_path: str) -> Item | None:
    """画像配信時にユーザー所有アイテムを画像パスから取得する。"""
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            _ITEM_SELECT + " WHERE i.user_id = %s AND i.image_path = %s" + _ITEM_GROUP_BY,
            (user_id, image_path),
        )
        row = cursor.fetchone()
        return _row_to_item(row) if row else None


def list_by_user(user_id: int, include_drafts: bool = True) -> list[Item]:
    """ユーザー所有アイテムを一覧取得する。"""
    sql = _ITEM_SELECT + " WHERE i.user_id = %s"
    params: list = [user_id]
    if not include_drafts:
        sql += " AND i.draft_flg = FALSE"
    sql += _ITEM_GROUP_BY + " ORDER BY i.updated_at DESC"

    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql, tuple(params))
        return [_row_to_item(row) for row in cursor.fetchall()]


def list_recent(user_id: int, limit: int = 5) -> list[Item]:
    """ホーム画面用に最近登録されたアイテムを取得する。"""
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            _ITEM_SELECT
            + " WHERE i.user_id = %s"
            + _ITEM_GROUP_BY
            + " ORDER BY i.created_at DESC LIMIT %s",
            (user_id, limit),
        )
        return [_row_to_item(row) for row in cursor.fetchall()]


def search(user_id: int, filters: dict) -> list[Item]:
    """検索条件に一致するユーザー所有アイテムをAND検索する。"""
    sql = _ITEM_SELECT + " WHERE i.user_id = %s"
    params: list = [user_id]

    keyword = filters.get("q")
    if keyword:
        # 動的検索条件でも値は必ずプレースホルダに渡し、SQLへ直接連結しない。
        like_keyword = f"%{keyword}%"
        sql += """
            AND (
                i.name LIKE %s
                OR s.name LIKE %s
                OR c.name LIKE %s
                OR ch.name LIKE %s
            )
        """
        params.extend([like_keyword] * 4)

    for key, column in (
        ("series_id", "i.series_id"),
        ("category_id", "i.category_id"),
    ):
        value = filters.get(key)
        if value:
            sql += f" AND {column} = %s"
            params.append(value)

    character_id = filters.get("character_id")
    if character_id:
        # キャラ条件はEXISTSで絞り込み、JOINによる同一アイテムの重複表示を避ける。
        sql += """
            AND EXISTS (
                SELECT 1
                FROM item_characters ic_filter
                INNER JOIN characters ch_filter
                  ON ch_filter.id = ic_filter.character_id
                WHERE ic_filter.item_id = i.id
                  AND ic_filter.character_id = %s
                  AND ch_filter.user_id = %s
            )
        """
        params.extend([character_id, user_id])

    delivery_status = filters.get("delivery_status")
    if delivery_status:
        sql += " AND i.delivery_status = %s"
        params.append(delivery_status)

    if not filters.get("include_drafts"):
        sql += " AND i.draft_flg = FALSE"

    sql += _ITEM_GROUP_BY + " ORDER BY i.updated_at DESC"

    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql, tuple(params))
        return [_row_to_item(row) for row in cursor.fetchall()]


def find_registered_by_identity(
    user_id: int,
    series_id: int | None,
    name: str,
    category_id: int | None,
    limit: int = 10,
) -> list[Item]:
    """シリーズ・商品名・カテゴリが一致する正式登録済みアイテムを取得する。"""
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            _ITEM_SELECT
            + """
             WHERE i.user_id = %s
               AND i.draft_flg = FALSE
               AND i.series_id <=> %s
               AND i.name = %s
               AND i.category_id <=> %s
            """
            + _ITEM_GROUP_BY
            + " ORDER BY i.updated_at DESC LIMIT %s",
            (user_id, series_id, name, category_id, limit),
        )
        return [_row_to_item(row) for row in cursor.fetchall()]


def find_registered_by_name(
    user_id: int, keyword: str, limit: int = 10
) -> list[Item]:
    """商品名の中間一致で正式登録済み候補を取得する。"""
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            _ITEM_SELECT
            + """
             WHERE i.user_id = %s
               AND i.draft_flg = FALSE
               AND (
                   i.name LIKE %s
                   OR %s LIKE CONCAT('%%', i.name, '%%')
               )
            """
            + _ITEM_GROUP_BY
            + " ORDER BY i.updated_at DESC LIMIT %s",
            (user_id, f"%{keyword}%", keyword, limit),
        )
        return [_row_to_item(row) for row in cursor.fetchall()]


def count_all(user_id: int) -> int:
    """正式登録済みアイテム数を取得する。"""
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
    brand_id: int | None = None,
    series_id: int | None = None,
    category_id: int | None = None,
    character_ids: list[int] | None = None,
    memo: str | None = None,
    image_path: str | None = None,
    delivery_status: str = "delivered",
    expected_delivery_date: date | None = None,
    delivery_reminder_enabled: bool = False,
) -> int:
    """アイテム本体とキャラ紐づけを同一トランザクションで登録する。"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO items (
                user_id, series_id, category_id, name, quantity, draft_flg,
                purchase_date, price, purchase_route_code, purchase_url,
                store_id, brand_id, memo, image_path, delivery_status,
                expected_delivery_date, delivery_reminder_enabled
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                user_id,
                series_id,
                category_id,
                name,
                quantity,
                draft_flg,
                purchase_date,
                price,
                purchase_route_code,
                purchase_url,
                store_id,
                brand_id,
                memo,
                image_path,
                delivery_status,
                expected_delivery_date,
                delivery_reminder_enabled,
            ),
        )
        item_id = cursor.lastrowid
        replace_item_characters(cursor, user_id, item_id, character_ids or [])
        return item_id


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
    brand_id: int | None = None,
    series_id: int | None = None,
    category_id: int | None = None,
    character_ids: list[int] | None = None,
    memo: str | None = None,
    image_path: str | None = None,
    delivery_status: str = "delivered",
    expected_delivery_date: date | None = None,
    delivery_reminder_enabled: bool = False,
) -> bool:
    """ユーザー所有アイテム本体とキャラ紐づけを同一トランザクションで更新する。"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM items WHERE id = %s AND user_id = %s",
            (item_id, user_id),
        )
        if not cursor.fetchone():
            return False

        cursor.execute(
            """
            UPDATE items SET
                series_id = %s, category_id = %s,
                name = %s, quantity = %s, draft_flg = %s,
                purchase_date = %s, price = %s,
                purchase_route_code = %s, purchase_url = %s,
                store_id = %s, brand_id = %s,
                memo = %s, image_path = %s,
                delivery_status = %s, expected_delivery_date = %s,
                delivery_reminder_enabled = %s, updated_at = %s
            WHERE id = %s AND user_id = %s
            """,
            (
                series_id,
                category_id,
                name,
                quantity,
                draft_flg,
                purchase_date,
                price,
                purchase_route_code,
                purchase_url,
                store_id,
                brand_id,
                memo,
                image_path,
                delivery_status,
                expected_delivery_date,
                delivery_reminder_enabled,
                datetime.now(),
                item_id,
                user_id,
            ),
        )
        replace_item_characters(cursor, user_id, item_id, character_ids or [])
        return True


def delete(user_id: int, item_id: int) -> bool:
    """Delete one item owned by the user."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM items WHERE id = %s AND user_id = %s",
            (item_id, user_id),
        )
        return cursor.rowcount > 0


def replace_item_characters(
    cursor, user_id: int, item_id: int, character_ids: list[int]
) -> None:
    """アイテムとキャラの多対多紐づけを差し替える。"""
    cursor.execute(
        """
        DELETE ic
          FROM item_characters ic
          INNER JOIN items i ON i.id = ic.item_id
         WHERE ic.item_id = %s
           AND i.user_id = %s
        """,
        (item_id, user_id),
    )
    if not character_ids:
        return

    # Service層で所有チェック済みだが、INSERT時もユーザー所有キャラだけに限定する。
    cursor.executemany(
        """
        INSERT INTO item_characters (item_id, character_id)
        SELECT %s, id
          FROM characters
         WHERE id = %s
           AND user_id = %s
        """,
        [(item_id, character_id, user_id) for character_id in character_ids],
    )


def list_character_ids(user_id: int, item_id: int) -> list[int]:
    """ユーザー所有アイテムに紐づくキャラIDを取得する。"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT ic.character_id
            FROM item_characters ic
            INNER JOIN items i ON i.id = ic.item_id
            WHERE i.user_id = %s AND ic.item_id = %s
            """,
            (user_id, item_id),
        )
        return [row[0] for row in cursor.fetchall()]


def list_deliveries(user_id: int, status: str | None = None) -> list[Item]:
    """配送管理画面に表示するユーザー所有アイテムを取得する。"""
    sql = _ITEM_SELECT + """
        WHERE i.user_id = %s
          AND i.draft_flg = FALSE
    """
    params: list = [user_id]
    if status:
        sql += " AND i.delivery_status = %s"
        params.append(status)
    else:
        sql += " AND i.delivery_status IN ('pending', 'shipped')"
    sql += (
        _ITEM_GROUP_BY
        + " ORDER BY i.expected_delivery_date IS NULL, i.expected_delivery_date, i.updated_at DESC"
    )

    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql, tuple(params))
        return [_row_to_item(row) for row in cursor.fetchall()]


def update_delivery(
    user_id: int,
    item_id: int,
    delivery_status: str,
    expected_delivery_date: date | None = None,
    delivery_reminder_enabled: bool = False,
) -> bool:
    """ユーザー所有アイテムの配送情報だけを更新する。"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE items
               SET delivery_status = %s,
                   expected_delivery_date = %s,
                   delivery_reminder_enabled = %s,
                   updated_at = %s
             WHERE id = %s AND user_id = %s
            """,
            (
                delivery_status,
                expected_delivery_date,
                delivery_reminder_enabled,
                datetime.now(),
                item_id,
                user_id,
            ),
        )
        return cursor.rowcount > 0


def increase_quantity(user_id: int, item_id: int, amount: int) -> bool:
    """ユーザー所有の正式登録済みアイテムの所持数を加算する。"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE items
               SET quantity = quantity + %s,
                   updated_at = %s
             WHERE id = %s
               AND user_id = %s
               AND draft_flg = FALSE
            """,
            (amount, datetime.now(), item_id, user_id),
        )
        return cursor.rowcount > 0


def sum_spending_for_month(user_id: int, year: int, month: int) -> Decimal:
    """指定月の正式登録済みアイテム購入金額を集計する。"""
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
