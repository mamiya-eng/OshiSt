from datetime import date

from oshist.dao import item_dao
from oshist.utils.validators import is_valid_delivery_status


class DeliveryService:
    """配送管理の入力検証と更新処理を扱う。"""

    def list_deliveries(self, user_id: int, status: str | None = None) -> list:
        """配送管理画面に表示するアイテムを取得する。"""
        if status and not is_valid_delivery_status(status):
            raise ValueError("配送ステータスの指定が不正です。")
        return item_dao.list_deliveries(user_id, status)

    def parse_update_form(self, form) -> dict:
        """配送更新フォームを検証して辞書へ変換する。"""
        delivery_status = (form.get("delivery_status") or "").strip()
        if not is_valid_delivery_status(delivery_status):
            raise ValueError("配送ステータスの指定が不正です。")

        expected_delivery_date = None
        date_raw = (form.get("expected_delivery_date") or "").strip()
        if date_raw:
            try:
                expected_delivery_date = date.fromisoformat(date_raw)
            except ValueError as exc:
                raise ValueError("配送予定日の日付形式が正しくありません。") from exc

        return {
            "delivery_status": delivery_status,
            "expected_delivery_date": expected_delivery_date,
            "delivery_reminder_enabled": form.get("delivery_reminder_enabled") == "on",
        }

    def update_delivery(self, user_id: int, item_id: int, data: dict) -> bool:
        """ユーザー所有アイテムの配送情報を更新する。"""
        return item_dao.update_delivery(
            user_id=user_id,
            item_id=item_id,
            delivery_status=data["delivery_status"],
            expected_delivery_date=data["expected_delivery_date"],
            delivery_reminder_enabled=data["delivery_reminder_enabled"],
        )
