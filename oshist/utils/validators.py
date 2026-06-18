import re
from urllib.parse import urlparse

from config import Config

ACCENT_COLOR_PATTERN = re.compile(r"^#[0-9A-Fa-f]{6}$")
URL_PATTERN = re.compile(r"^https?://", re.IGNORECASE)

PURCHASE_ROUTE_LABELS = {
    "physical_store": "店舗",
    "web_store": "Webストア",
    "flea_market": "フリマ",
    "event": "イベント",
    "exchange": "交換",
    "gift": "プレゼント",
    "other": "その他",
}

DELIVERY_STATUS_LABELS = {
    "pending": "発送待ち",
    "shipped": "発送済み",
    "delivered": "配達完了",
    "cancelled": "キャンセル",
}


def is_valid_accent_color(value: str | None) -> bool:
    """推しカラーが #RRGGBB 形式か判定する。"""
    return bool(value and ACCENT_COLOR_PATTERN.match(value))


def is_valid_purchase_route(code: str | None) -> bool:
    """購入ルートコードが許可値か判定する。"""
    return code in Config.PURCHASE_ROUTE_CODES


def is_valid_purchase_url(url: str | None) -> bool:
    """購入URLがhttpまたはhttpsだけを使っているか判定する。"""
    if not url:
        return True
    stripped_url = url.strip()
    parsed = urlparse(stripped_url)
    if parsed.scheme.lower() not in ("http", "https"):
        return False
    return bool(URL_PATTERN.match(stripped_url))


def is_valid_delivery_status(status: str | None) -> bool:
    """配送ステータスが許可値か判定する。"""
    return status in Config.DELIVERY_STATUSES
