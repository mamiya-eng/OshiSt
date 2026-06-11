from datetime import date
from decimal import Decimal, InvalidOperation

from oshist.dao import item_dao, store_dao
from oshist.utils.validators import (
    PURCHASE_ROUTE_LABELS,
    is_valid_delivery_status,
    is_valid_purchase_route,
    is_valid_purchase_url,
)


class ItemService:
    def parse_form(self, user_id: int, form, files=None) -> dict:
        name = (form.get("name") or "").strip()
        if not name:
            raise ValueError("商品名は必須です。")

        quantity_raw = (form.get("quantity") or "1").strip()
        try:
            quantity = int(quantity_raw)
        except ValueError as exc:
            raise ValueError("数量は整数で入力してください。") from exc
        if quantity < 1:
            raise ValueError("数量は1以上で入力してください。")

        action = form.get("action", "draft")
        draft_flg = action == "draft"

        purchase_date = None
        purchase_date_raw = (form.get("purchase_date") or "").strip()
        if purchase_date_raw:
            purchase_date = date.fromisoformat(purchase_date_raw)

        price = None
        price_raw = (form.get("price") or "").strip()
        if price_raw:
            try:
                price = Decimal(price_raw)
            except InvalidOperation as exc:
                raise ValueError("金額の形式が正しくありません。") from exc

        purchase_route_code = (form.get("purchase_route_code") or "").strip() or None
        if purchase_route_code and not is_valid_purchase_route(purchase_route_code):
            raise ValueError("購入ルートの値が不正です。")

        purchase_url = (form.get("purchase_url") or "").strip() or None
        if purchase_url and not is_valid_purchase_url(purchase_url):
            raise ValueError("URLは http / https のみ許可されます。")

        store_id = None
        store_name = (form.get("store_name") or "").strip()
        if store_name:
            store_id = store_dao.find_or_create(user_id, store_name)

        memo = (form.get("memo") or "").strip() or None

        delivery_status = "delivered"
        if form.get("is_preorder") == "on":
            delivery_status = "pending"
        if not is_valid_delivery_status(delivery_status):
            raise ValueError("配送ステータスが不正です。")

        if not draft_flg:
            if purchase_date is None:
                raise ValueError("本登録には購入日が必要です。")
            if purchase_route_code is None:
                raise ValueError("本登録には購入ルートが必要です。")

        return {
            "name": name,
            "quantity": quantity,
            "draft_flg": draft_flg,
            "purchase_date": purchase_date,
            "price": price,
            "purchase_route_code": purchase_route_code,
            "purchase_url": purchase_url,
            "store_id": store_id,
            "memo": memo,
            "delivery_status": delivery_status,
            "image_file": files.get("image") if files else None,
        }

    def create_item(self, user_id: int, data: dict, image_path: str | None = None) -> int:
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
            memo=data["memo"],
            image_path=image_path,
            delivery_status=data["delivery_status"],
        )

    def update_item(
        self, user_id: int, item_id: int, data: dict, image_path: str | None
    ) -> bool:
        existing = item_dao.find_by_id(user_id, item_id)
        if not existing:
            return False
        final_image = image_path or existing.image_path
        return item_dao.update(
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
            memo=data["memo"],
            image_path=final_image,
            delivery_status=data["delivery_status"],
        )

    @staticmethod
    def purchase_route_label(code: str | None) -> str:
        if not code:
            return "-"
        return PURCHASE_ROUTE_LABELS.get(code, code)
