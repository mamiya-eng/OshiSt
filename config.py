import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent


class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-in-production")
    PERMANENT_SESSION_LIFETIME = 1800  # 30分

    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER = os.getenv("MYSQL_USER", "oshist")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "oshist")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "oshist")

    UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", BASE_DIR / "uploads"))
    MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(5 * 1024 * 1024)))

    PURCHASE_ROUTE_CODES = frozenset(
        {
            "physical_store",
            "web_store",
            "flea_market",
            "event",
            "exchange",
            "gift",
            "other",
        }
    )

    DELIVERY_STATUSES = frozenset({"pending", "shipped", "delivered", "cancelled"})
