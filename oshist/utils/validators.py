import re
from urllib.parse import urlparse

from config import Config

ACCENT_COLOR_PATTERN = re.compile(r"^#[0-9A-Fa-f]{6}$")
URL_PATTERN = re.compile(r"^https?://", re.IGNORECASE)

PURCHASE_ROUTE_LABELS = {
    "physical_store": "店舗",
    "web_store": "WEBストア",
    "flea_market": "フリマ",
    "event": "イベント",
    "exchange": "交換",
    "gift": "プレゼント",
    "other": "その他",
}


def is_valid_accent_color(value: str | None) -> bool:
    return bool(value and ACCENT_COLOR_PATTERN.match(value))


def is_valid_purchase_route(code: str | None) -> bool:
    return code in Config.PURCHASE_ROUTE_CODES


def is_valid_purchase_url(url: str | None) -> bool:
    if not url:
        return True
    parsed = urlparse(url.strip())
    if parsed.scheme.lower() not in ("http", "https"):
        return False
    return bool(URL_PATTERN.match(url.strip()))


def is_valid_delivery_status(status: str | None) -> bool:
    return status in Config.DELIVERY_STATUSES
