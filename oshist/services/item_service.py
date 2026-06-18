from datetime import date
from decimal import Decimal, InvalidOperation

from oshist.dao import brand_dao, category_dao, character_dao, item_dao, series_dao, store_dao
from oshist.utils.image import delete_uploaded_image
from oshist.utils.validators import (
    PURCHASE_ROUTE_LABELS,
    is_valid_delivery_status,
    is_valid_purchase_route,
    is_valid_purchase_url,
)


class ItemService:
    """アイテム登録・編集・検索の入力検証を扱う。"""

    def parse_form(self, user_id: int, form, files=None) -> dict:
        """アイテム登録・編集フォームを検証して辞書へ変換する。"""
        name = (form.get("name") or "").strip()
        if not name:
            raise ValueError("商品名は必須です。")
        if len(name) > 200:
            raise ValueError("商品名は200文字以内で入力してください。")

        quantity = self._parse_quantity(form.get("quantity"))
        draft_flg = form.get("action", "draft") == "draft"
        purchase_date = self._optional_date(form.get("purchase_date"), "購入日")
        expected_delivery_date = self._optional_date(
            form.get("expected_delivery_date"), "配送予定日"
        )
        price = self._optional_price(form.get("price"))

        purchase_route_code = (form.get("purchase_route_code") or "").strip() or None
        if purchase_route_code and not is_valid_purchase_route(purchase_route_code):
            raise ValueError("購入ルートの値が不正です。")

        purchase_url = (form.get("purchase_url") or "").strip() or None
        if purchase_url and not is_valid_purchase_url(purchase_url):
            raise ValueError("URLは http / https のみ許可されています。")

        store_id = None
        store_name = (form.get("store_name") or "").strip()
        if store_name:
            store_id = store_dao.find_or_create(user_id, store_name)

        brand_id = None
        brand_name = (form.get("brand_name") or "").strip()
        if brand_name:
            brand_id = brand_dao.find_or_create(user_id, brand_name)

        barcode = (form.get("barcode") or "").strip() or None
        if barcode and len(barcode) > 100:
            raise ValueError("バーコードは100文字以内で入力してください。")

        series_id = self._optional_owned_id(
            user_id, form.get("series_id"), series_dao.find_by_id, "シリーズ"
        )
        category_id = self._optional_owned_id(
            user_id, form.get("category_id"), category_dao.find_by_id, "カテゴリ"
        )
        character_ids = self._owned_character_ids(user_id, form.getlist("character_ids"))
        delivery_status = self._delivery_status(form)

        return {
            "name": name,
            "quantity": quantity,
            "draft_flg": draft_flg,
            "purchase_date": purchase_date,
            "price": price,
            "purchase_route_code": purchase_route_code,
            "purchase_url": purchase_url,
            "store_id": store_id,
            "brand_id": brand_id,
            "barcode": barcode,
            "series_id": series_id,
            "category_id": category_id,
            "character_ids": character_ids,
            "memo": (form.get("memo") or "").strip() or None,
            "delivery_status": delivery_status,
            "expected_delivery_date": expected_delivery_date,
            "delivery_reminder_enabled": form.get("delivery_reminder_enabled") == "on",
            "image_file": files.get("image") if files else None,
        }

    @staticmethod
    def _parse_quantity(raw_value: str | None) -> int:
        """数量を1以上の整数として検証する。"""
        quantity_raw = (raw_value or "1").strip() or "1"
        try:
            quantity = int(quantity_raw)
        except ValueError as exc:
            raise ValueError("数量は整数で入力してください。") from exc
        if quantity < 1:
            raise ValueError("数量は1以上で入力してください。")
        return quantity

    @staticmethod
    def _optional_price(raw_value: str | None) -> Decimal | None:
        """未入力をNULLとして扱い、入力時は0以上の金額として検証する。"""
        price_raw = (raw_value or "").strip()
        if not price_raw:
            return None
        try:
            price = Decimal(price_raw)
        except InvalidOperation as exc:
            raise ValueError("金額の形式が正しくありません。") from exc
        if price < 0:
            raise ValueError("金額は0円以上で入力してください。")
        return price

    @staticmethod
    def _optional_date(raw_value: str | None, label: str) -> date | None:
        """未入力をNULLとして扱い、入力時はISO形式の日付として検証する。"""
        value = (raw_value or "").strip()
        if not value:
            return None
        try:
            return date.fromisoformat(value)
        except ValueError as exc:
            raise ValueError(f"{label}の日付形式が正しくありません。") from exc

    @staticmethod
    def _optional_owned_id(user_id: int, raw_value: str | None, finder, label: str) -> int | None:
        """POSTされたIDがログインユーザーの所有データか確認する。"""
        if not raw_value:
            return None
        try:
            value = int(raw_value)
        except ValueError as exc:
            raise ValueError(f"{label}の指定が不正です。") from exc

        # IDはフォーム側で改ざんできるため、必ずuser_id付きで所有者チェックする。
        if not finder(user_id, value):
            raise ValueError(f"指定された{label}が見つかりません。")
        return value

    @staticmethod
    def _owned_character_ids(user_id: int, raw_values: list[str]) -> list[int]:
        """複数選択されたキャラIDがユーザー所有データか確認する。"""
        character_ids: list[int] = []
        for raw_value in raw_values:
            if not raw_value:
                continue
            try:
                character_id = int(raw_value)
            except ValueError as exc:
                raise ValueError("キャラの指定が不正です。") from exc
            if not character_dao.find_by_id(user_id, character_id):
                raise ValueError("指定されたキャラが見つかりません。")
            if character_id not in character_ids:
                character_ids.append(character_id)
        return character_ids

    @staticmethod
    def _delivery_status(form) -> str:
        """配送ステータスを許可値に限定する。"""
        if form.get("is_reserved") == "on" or form.get("is_preorder") == "on":
            return "pending"

        delivery_status = (form.get("delivery_status") or "").strip()
        if not delivery_status:
            delivery_status = "delivered"
        if not is_valid_delivery_status(delivery_status):
            raise ValueError("配送ステータスが不正です。")
        return delivery_status

    def create_item(self, user_id: int, data: dict, image_path: str | None = None) -> int:
        """アイテムを登録する。"""
        return item_dao.create(
            user_id=user_id,
            name=data["name"],
            quantity=data["quantity"],
            draft_flg=data["draft_flg"],
            purchase_date=data["purchase_date"],
            price=data["price"],
            purchase_route_code=data["purchase_route_code"],
            purchase_url=data["purchase_url"],
            store_id=data["store_id"],
            brand_id=data["brand_id"],
            barcode=data["barcode"],
            series_id=data["series_id"],
            category_id=data["category_id"],
            character_ids=data["character_ids"],
            memo=data["memo"],
            image_path=image_path,
            delivery_status=data["delivery_status"],
            expected_delivery_date=data["expected_delivery_date"],
            delivery_reminder_enabled=data["delivery_reminder_enabled"],
        )

    def update_item(
        self, user_id: int, item_id: int, data: dict, image_path: str | None
    ) -> bool:
        """ユーザー所有アイテムを更新する。"""
        existing = item_dao.find_by_id(user_id, item_id)
        if not existing:
            if image_path:
                delete_uploaded_image(image_path)
            return False
        final_image = image_path or existing.image_path
        try:
            updated = item_dao.update(
                user_id=user_id,
                item_id=item_id,
                name=data["name"],
                quantity=data["quantity"],
                draft_flg=data["draft_flg"],
                purchase_date=data["purchase_date"],
                price=data["price"],
                purchase_route_code=data["purchase_route_code"],
                purchase_url=data["purchase_url"],
                store_id=data["store_id"],
                brand_id=data["brand_id"],
                barcode=data["barcode"],
                series_id=data["series_id"],
                category_id=data["category_id"],
                character_ids=data["character_ids"],
                memo=data["memo"],
                image_path=final_image,
                delivery_status=data["delivery_status"],
                expected_delivery_date=data["expected_delivery_date"],
                delivery_reminder_enabled=data["delivery_reminder_enabled"],
            )
        except Exception:
            if image_path:
                delete_uploaded_image(image_path)
            raise

        if not updated:
            if image_path:
                delete_uploaded_image(image_path)
            return False
        if image_path and existing.image_path and existing.image_path != image_path:
            delete_uploaded_image(existing.image_path)
        return True

    def delete_item(self, user_id: int, item_id: int) -> bool:
        """Delete a user-owned item and then remove its image file."""
        existing = item_dao.find_by_id(user_id, item_id)
        if not existing:
            return False

        deleted = item_dao.delete(user_id, item_id)
        if deleted and existing.image_path:
            delete_uploaded_image(existing.image_path)
        return deleted

    def parse_search_filters(self, user_id: int, form) -> dict:
        """アイテム検索条件を検証して辞書へ変換する。"""
        filters = {
            "q": (form.get("q") or "").strip() or None,
            "include_drafts": form.get("include_drafts") == "on",
        }
        finder_by_key = {
            "series_id": (series_dao.find_by_id, "シリーズ"),
            "category_id": (category_dao.find_by_id, "カテゴリ"),
            "character_id": (character_dao.find_by_id, "キャラ"),
        }
        for key, (finder, label) in finder_by_key.items():
            value = (form.get(key) or "").strip()
            if value:
                filters[key] = self._optional_owned_id(user_id, value, finder, label)

        delivery_status = (form.get("delivery_status") or "").strip()
        if delivery_status:
            if not is_valid_delivery_status(delivery_status):
                raise ValueError("配送ステータスの指定が不正です。")
            filters["delivery_status"] = delivery_status
        return filters

    @staticmethod
    def purchase_route_label(code: str | None) -> str:
        """購入ルートコードを画面表示用ラベルへ変換する。"""
        if not code:
            return "-"
        return PURCHASE_ROUTE_LABELS.get(code, code)
