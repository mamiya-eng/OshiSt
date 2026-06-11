from datetime import date
from decimal import Decimal, InvalidOperation

from oshist.dao import budget_dao, item_dao
from oshist.models import BudgetSummary


class BudgetService:
    def get_monthly_summary(self, user_id: int, year: int, month: int) -> BudgetSummary | None:
        budget = budget_dao.find_for_month(user_id, year, month)
        if not budget:
            return None

        used = item_dao.sum_spending_for_month(user_id, year, month)
        remaining = budget.amount - used
        usage_rate = float(used / budget.amount * 100) if budget.amount > 0 else 0.0

        return BudgetSummary(
            budget_amount=budget.amount,
            used_amount=used,
            remaining_amount=remaining,
            usage_rate=usage_rate,
        )

    def save_budget(self, user_id: int, year: int, month: int, amount_raw: str) -> None:
        if not (1 <= month <= 12):
            raise ValueError("月は1〜12で指定してください。")

        try:
            amount = Decimal(amount_raw.strip())
        except (InvalidOperation, AttributeError) as exc:
            raise ValueError("予算額の形式が正しくありません。") from exc

        if amount <= 0:
            raise ValueError("予算額は1円以上で設定してください。")

        if budget_dao.find_for_month(user_id, year, month):
            budget_dao.upsert(user_id, year, month, amount)
            return

        budget_dao.upsert(user_id, year, month, amount)

    def motivational_message(self, summary: BudgetSummary) -> str | None:
        if summary.remaining_amount < 0:
            return "今月は推しへの愛が予算を超えています"
        if summary.usage_rate >= 80:
            return "今月はまだ余裕がありますが、来月は推しへの投資を控えめに"
        return None

    @staticmethod
    def current_year_month() -> tuple[int, int]:
        today = date.today()
        return today.year, today.month
