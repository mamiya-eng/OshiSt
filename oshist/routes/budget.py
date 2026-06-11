from flask import Blueprint, flash, redirect, render_template, request, url_for

from oshist.services.budget_service import BudgetService
from oshist.services.dashboard_service import DashboardService
from oshist.utils.auth import get_current_user_id, login_required
from oshist.utils.csrf import validate_csrf_token

budget_bp = Blueprint("budget", __name__, url_prefix="/budget")
budget_service = BudgetService()


@budget_bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    user_id = get_current_user_id()
    year, month = budget_service.current_year_month()

    if request.method == "POST":
        if not validate_csrf_token(request.form.get("csrf_token")):
            return ("Forbidden", 403)
        try:
            year = int(request.form.get("year", year))
            month = int(request.form.get("month", month))
            budget_service.save_budget(
                user_id, year, month, request.form.get("amount", "")
            )
            flash("予算を保存しました。", "success")
            return redirect(url_for("budget.index", year=year, month=month))
        except ValueError as exc:
            flash(str(exc), "error")

    year = int(request.args.get("year", year))
    month = int(request.args.get("month", month))
    summary = budget_service.get_monthly_summary(user_id, year, month)
    message = budget_service.motivational_message(summary) if summary else None

    return render_template(
        "budget/index.html",
        year=year,
        month=month,
        summary=summary,
        message=message,
        format_yen=DashboardService.format_yen,
    )
