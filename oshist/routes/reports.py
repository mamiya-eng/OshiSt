from flask import Blueprint, render_template, request

from oshist.services.report_service import ReportService
from oshist.utils.auth import get_current_user_id, login_required

reports_bp = Blueprint("reports", __name__, url_prefix="/reports")
report_service = ReportService()


@reports_bp.route("/")
@login_required
def index():
    """ログインユーザーの支出グラフを表示する。"""
    report = report_service.get_report(
        get_current_user_id(), request.args.get("year")
    )
    return render_template("reports/index.html", **report)


@reports_bp.route("/yearly")
@login_required
def yearly():
    """ログインユーザーの年間レポートを表示する。"""
    report = report_service.get_yearly_report(
        get_current_user_id(), request.args.get("year")
    )
    return render_template("reports/yearly.html", **report)
