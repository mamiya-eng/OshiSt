from datetime import date
from decimal import Decimal

from oshist.dao import item_dao
from oshist.services.budget_service import BudgetService


class DashboardService:
    def __init__(self):
        self.budget_service = BudgetService()

    def get_home_data(self, user_id: int) -> dict:
        today = date.today()
        year, month = today.year, today.month

        total_items = item_dao.count_all(user_id)
        recent_items = item_dao.list_recent(user_id, limit=5)
        monthly_spending = item_dao.sum_spending_for_month(user_id, year, month)
        budget_summary = self.budget_service.get_monthly_summary(user_id, year, month)

        message = None
        if budget_summary:
            message = self.budget_service.motivational_message(budget_summary)

        return {
            "year": year,
            "month": month,
            "total_items": total_items,
            "recent_items": recent_items,
            "monthly_spending": monthly_spending,
            "budget_summary": budget_summary,
            "budget_message": message,
        }

    @staticmethod
    def format_yen(value: Decimal | int | float) -> str:
        amount = int(value)
        return f"{amount:,}円"
