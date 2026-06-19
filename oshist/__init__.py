from flask import Flask

from config import Config
from oshist.routes.auth import auth_bp
from oshist.routes.budget import budget_bp
from oshist.routes.delivery import delivery_bp
from oshist.routes.home import home_bp
from oshist.routes.images import images_bp
from oshist.routes.items import items_bp
from oshist.routes.masters import masters_bp
from oshist.services.dashboard_service import DashboardService


def create_app(config_class=Config):
    """Flaskアプリを生成し、利用するBlueprintを登録する。"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    config_class.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    app.register_blueprint(auth_bp)
    app.register_blueprint(home_bp)
    app.register_blueprint(items_bp)
    app.register_blueprint(masters_bp)
    app.register_blueprint(delivery_bp)
    app.register_blueprint(budget_bp)
    app.register_blueprint(images_bp)
    app.add_template_filter(DashboardService.format_yen, "yen")

    @app.context_processor
    def inject_csrf_token():
        """テンプレートからCSRFトークン生成関数を呼べるようにする。"""
        from oshist.utils.csrf import generate_csrf_token

        return {"csrf_token": generate_csrf_token}

    return app
