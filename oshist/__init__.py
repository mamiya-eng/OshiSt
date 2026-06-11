from flask import Flask

from config import Config
from oshist.routes.auth import auth_bp
from oshist.routes.budget import budget_bp
from oshist.routes.home import home_bp
from oshist.routes.images import images_bp
from oshist.routes.items import items_bp


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    config_class.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    app.register_blueprint(auth_bp)
    app.register_blueprint(home_bp)
    app.register_blueprint(items_bp)
    app.register_blueprint(budget_bp)
    app.register_blueprint(images_bp)

    @app.context_processor
    def inject_csrf_token():
        from oshist.utils.csrf import generate_csrf_token

        return {"csrf_token": generate_csrf_token}

    return app
