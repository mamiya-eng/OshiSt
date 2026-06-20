from datetime import date

from oshist.dao import report_dao


class ReportService:
    """支出グラフ用の年選択・集計データ整形を扱う。"""

    @staticmethod
    def parse_year(raw_year: str | None) -> int:
        current_year = date.today().year
        if not raw_year:
            return current_year
        try:
            year = int(raw_year)
        except (TypeError, ValueError):
            return current_year
        if not 1900 <= year <= 2100:
            return current_year
        return year

    def get_report(self, user_id: int, raw_year: str | None) -> dict:
        year = self.parse_year(raw_year)
        available_years = report_dao.list_purchase_years(user_id)
        if year not in available_years:
            available_years.append(year)
        available_years = sorted(set(available_years), reverse=True)

        monthly_rows = report_dao.monthly_spending(user_id, year)
        monthly_by_number = {
            int(row["month"]): report_dao.decimal_amount(row["amount"])
            for row in monthly_rows
        }
        monthly_amounts = [
            int(monthly_by_number.get(month, 0)) for month in range(1, 13)
        ]

        series_rows = report_dao.series_spending(user_id, year, limit=10)
        category_rows = report_dao.category_spending(user_id, year, limit=10)
        series_labels = [row["label"] for row in series_rows]
        series_amounts = [
            int(report_dao.decimal_amount(row["amount"])) for row in series_rows
        ]
        category_labels = [row["label"] for row in category_rows]
        category_amounts = [
            int(report_dao.decimal_amount(row["amount"])) for row in category_rows
        ]

        total_amount = sum(monthly_amounts)
        top_month_index = max(range(12), key=monthly_amounts.__getitem__)
        top_month = (
            {"label": f"{top_month_index + 1}月", "amount": monthly_amounts[top_month_index]}
            if monthly_amounts[top_month_index] > 0
            else None
        )
        top_series = (
            {"label": series_labels[0], "amount": series_amounts[0]}
            if series_labels
            else None
        )
        top_category = (
            {"label": category_labels[0], "amount": category_amounts[0]}
            if category_labels
            else None
        )

        return {
            "year": year,
            "available_years": available_years or [date.today().year],
            "has_data": bool(monthly_rows),
            "total_amount": total_amount,
            "top_month": top_month,
            "top_series": top_series,
            "top_category": top_category,
            "monthly_chart": {
                "labels": [f"{month}月" for month in range(1, 13)],
                "amounts": monthly_amounts,
            },
            "series_chart": {
                "labels": series_labels,
                "amounts": series_amounts,
            },
            "category_chart": {
                "labels": category_labels,
                "amounts": category_amounts,
            },
        }

    def get_yearly_report(self, user_id: int, raw_year: str | None) -> dict:
        """Build the annual report using the existing graph aggregates."""
        report = self.get_report(user_id, raw_year)
        year = report["year"]

        counts = report_dao.yearly_item_counts(user_id, year)
        item_count = int(counts["item_count"] or 0)
        total_quantity = int(counts["total_quantity"] or 0)

        top_purchases = report_dao.top_purchases(user_id, year, limit=5)
        for purchase in top_purchases:
            purchase["amount"] = int(
                report_dao.decimal_amount(purchase["amount"])
            )

        category_counts = report_dao.category_purchase_counts(
            user_id, year, limit=5
        )
        for category in category_counts:
            category["item_count"] = int(category["item_count"] or 0)

        has_yearly_data = item_count > 0
        if has_yearly_data:
            narrative = (
                f"{year}年は合計{report['total_amount']:,}円の"
                "推し活支出がありました。"
            )
            if report["top_month"]:
                narrative += (
                    f" 特に{report['top_month']['label']}の使用額が"
                    "もっとも多くなりました。"
                )
            if (
                report["top_series"]
                and report["top_series"]["label"] != "未設定"
            ):
                narrative += (
                    f" {report['top_series']['label']}関連の購入が"
                    "支出の上位でした。"
                )
        else:
            narrative = "この年の購入データはまだありません"

        report.update(
            {
                "has_yearly_data": has_yearly_data,
                "item_count": item_count,
                "total_quantity": total_quantity,
                "top_purchases": top_purchases,
                "category_purchase_counts": category_counts,
                "narrative": narrative,
                "monthly_rows": [
                    {"label": label, "amount": amount}
                    for label, amount in zip(
                        report["monthly_chart"]["labels"],
                        report["monthly_chart"]["amounts"],
                    )
                ],
            }
        )
        return report
