from flask import Blueprint, render_template

from oshist.services.dashboard_service import DashboardService
from oshist.utils.auth import get_current_user_id, login_required

home_bp = Blueprint("home", __name__)
dashboard_service = DashboardService()


@home_bp.route("/")
@login_required
def index():
    user_id = get_current_user_id()
    data = dashboard_service.get_home_data(user_id)
    return render_template("home.html", **data, format_yen=DashboardService.format_yen)
