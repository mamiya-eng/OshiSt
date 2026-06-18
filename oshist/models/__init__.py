from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal


@dataclass
class User:
    id: int
    name: str
    password_hash: str
    theme_type: str = "simple"
    accent_color: str = "#4A90D9"


@dataclass
class Item:
    id: int
    user_id: int
    name: str
    quantity: int
    draft_flg: bool
    delivery_status: str
    created_at: datetime
    updated_at: datetime
    series_id: int | None = None
    category_id: int | None = None
    purchase_date: date | None = None
    price: Decimal | None = None
    memo: str | None = None
    image_path: str | None = None
    barcode: str | None = None
    store_id: int | None = None
    brand_id: int | None = None
    purchase_route_code: str | None = None
    purchase_url: str | None = None
    favorite: bool = False
    expected_delivery_date: date | None = None
    delivery_reminder_enabled: bool = False
    series_name: str | None = None
    category_name: str | None = None
    store_name: str | None = None
    brand_name: str | None = None
    character_names: str | None = None


@dataclass
class Budget:
    id: int
    user_id: int
    year: int
    month: int
    amount: Decimal
    target_series_id: int | None = None
    target_character_id: int | None = None


@dataclass
class BudgetSummary:
    budget_amount: Decimal
    used_amount: Decimal
    remaining_amount: Decimal
    usage_rate: float
