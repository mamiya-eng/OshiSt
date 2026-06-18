from oshist.dao import category_dao, character_dao, series_dao
from oshist.utils.validators import is_valid_accent_color


class MasterService:
    """シリーズ・カテゴリ・キャラ管理の入力検証と業務ルールを扱う。"""

    @staticmethod
    def _required_name(form, label: str) -> str:
        """名称の必須チェックと文字数チェックを行う。"""
        name = (form.get("name") or "").strip()
        if not name:
            raise ValueError(f"{label}名を入力してください。")
        if len(name) > 100:
            raise ValueError(f"{label}名は100文字以内で入力してください。")
        return name

    def parse_series_form(self, form) -> dict:
        """シリーズ登録・編集フォームを検証して辞書へ変換する。"""
        description = (form.get("description") or "").strip() or None
        return {
            "name": self._required_name(form, "シリーズ"),
            "description": description,
        }

    def parse_category_form(self, form) -> dict:
        """カテゴリ登録・編集フォームを検証して辞書へ変換する。"""
        return {"name": self._required_name(form, "カテゴリ")}

    def parse_character_form(self, user_id: int, form) -> dict:
        """キャラ登録・編集フォームを検証して辞書へ変換する。"""
        series_id = self._required_owned_series_id(user_id, form.get("series_id"))
        color = (form.get("color") or "").strip() or None
        if color and not is_valid_accent_color(color):
            raise ValueError("推しカラーは #RRGGBB 形式で入力してください。")

        return {
            "name": self._required_name(form, "キャラ"),
            "series_id": series_id,
            "color": color,
        }

    @staticmethod
    def _required_owned_series_id(user_id: int, raw_value: str | None) -> int:
        """POSTされたシリーズIDがログインユーザーの所有データか確認する。"""
        if not raw_value:
            raise ValueError("キャラは必ずシリーズに紐づけてください。")
        try:
            series_id = int(raw_value)
        except ValueError as exc:
            raise ValueError("シリーズの指定が不正です。") from exc

        # IDはフォーム側で改ざんできるため、必ずuser_id付きで所有者チェックする。
        if not series_dao.find_by_id(user_id, series_id):
            raise ValueError("指定されたシリーズが見つかりません。")
        return series_id

    def create_series(self, user_id: int, data: dict) -> int:
        """重複を確認してシリーズを登録する。"""
        if series_dao.find_by_name(user_id, data["name"]):
            raise ValueError("同じ名前のシリーズはすでに登録されています。")
        return series_dao.create(user_id, data["name"], data["description"])

    def update_series(self, user_id: int, series_id: int, data: dict) -> bool:
        """重複を確認してシリーズを更新する。"""
        if not series_dao.find_by_id(user_id, series_id):
            raise ValueError("更新対象のシリーズが見つかりません。")
        if series_dao.find_by_name(user_id, data["name"], exclude_series_id=series_id):
            raise ValueError("同じ名前のシリーズはすでに登録されています。")
        return series_dao.update(
            user_id, series_id, data["name"], data["description"]
        )

    def delete_series(self, user_id: int, series_id: int) -> bool:
        """未使用のシリーズだけ削除する。"""
        if not series_dao.find_by_id(user_id, series_id):
            raise ValueError("削除対象のシリーズが見つかりません。")
        if series_dao.count_items(user_id, series_id) > 0:
            raise ValueError("このシリーズはアイテムで使用中のため削除できません。")
        if series_dao.count_characters(user_id, series_id) > 0:
            raise ValueError("このシリーズはキャラで使用中のため削除できません。")
        return series_dao.delete(user_id, series_id)

    def create_category(self, user_id: int, data: dict) -> int:
        """重複を確認してカテゴリを登録する。"""
        if category_dao.find_by_name(user_id, data["name"]):
            raise ValueError("同じ名前のカテゴリはすでに登録されています。")
        return category_dao.create(user_id, data["name"])

    def update_category(self, user_id: int, category_id: int, data: dict) -> bool:
        """重複を確認してカテゴリを更新する。"""
        if not category_dao.find_by_id(user_id, category_id):
            raise ValueError("更新対象のカテゴリが見つかりません。")
        if category_dao.find_by_name(
            user_id, data["name"], exclude_category_id=category_id
        ):
            raise ValueError("同じ名前のカテゴリはすでに登録されています。")
        return category_dao.update(user_id, category_id, data["name"])

    def delete_category(self, user_id: int, category_id: int) -> bool:
        """未使用のカテゴリだけ削除する。"""
        if not category_dao.find_by_id(user_id, category_id):
            raise ValueError("削除対象のカテゴリが見つかりません。")
        if category_dao.count_items(user_id, category_id) > 0:
            raise ValueError("このカテゴリはアイテムで使用中のため削除できません。")
        return category_dao.delete(user_id, category_id)

    def create_character(self, user_id: int, data: dict) -> int:
        """重複を確認してキャラを登録する。"""
        if character_dao.find_by_name(user_id, data["series_id"], data["name"]):
            raise ValueError("同じシリーズ内に同じ名前のキャラが登録されています。")
        return character_dao.create(
            user_id, data["name"], data["series_id"], data["color"]
        )

    def update_character(self, user_id: int, character_id: int, data: dict) -> bool:
        """重複を確認してキャラを更新する。"""
        if not character_dao.find_by_id(user_id, character_id):
            raise ValueError("更新対象のキャラが見つかりません。")
        if character_dao.find_by_name(
            user_id,
            data["series_id"],
            data["name"],
            exclude_character_id=character_id,
        ):
            raise ValueError("同じシリーズ内に同じ名前のキャラが登録されています。")
        return character_dao.update(
            user_id,
            character_id,
            data["name"],
            data["series_id"],
            data["color"],
        )

    def delete_character(self, user_id: int, character_id: int) -> bool:
        """未使用のキャラだけ削除する。"""
        if not character_dao.find_by_id(user_id, character_id):
            raise ValueError("削除対象のキャラが見つかりません。")
        if character_dao.count_items(user_id, character_id) > 0:
            raise ValueError("このキャラはアイテムで使用中のため削除できません。")
        return character_dao.delete(user_id, character_id)
