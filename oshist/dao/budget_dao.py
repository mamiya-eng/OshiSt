from decimal import Decimal

from oshist.db import get_connection
from oshist.models import Budget


def find_for_month(
    user_id: int,
    year: int,
    month: int,
    target_series_id: int | None = None,
    target_character_id: int | None = None,
) -> Budget | None:
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, user_id, year, month, amount, target_series_id, target_character_id
            FROM budgets
            WHERE user_id = %s AND year = %s AND month = %s
              AND target_series_id <=> %s
              AND target_character_id <=> %s
            """,
            (user_id, year, month, target_series_id, target_character_id),
        )
        row = cursor.fetchone()
        return Budget(**row) if row else None


def upsert(
    user_id: int,
    year: int,
    month: int,
    amount: Decimal,
    target_series_id: int | None = None,
    target_character_id: int | None = None,
) -> None:
    existing = find_for_month(
        user_id, year, month, target_series_id, target_character_id
    )
    with get_connection() as conn:
        cursor = conn.cursor()
        if existing:
            cursor.execute(
                "UPDATE budgets SET amount = %s WHERE id = %s AND user_id = %s",
                (amount, existing.id, user_id),
            )
        else:
            cursor.execute(
                """
                INSERT INTO budgets (
                    user_id, year, month, amount, target_series_id, target_character_id
                ) VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (user_id, year, month, amount, target_series_id, target_character_id),
            )
