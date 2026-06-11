import bcrypt

from oshist.dao import user_dao


class AuthService:
    @staticmethod
    def hash_password(password: str) -> str:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))

    def register(self, name: str, password: str) -> int:
        name = name.strip()
        if not name:
            raise ValueError("ユーザー名は必須です。")
        if len(password) < 8:
            raise ValueError("パスワードは8文字以上で入力してください。")
        if user_dao.find_by_name(name):
            raise ValueError("このユーザー名は既に使われています。")
        password_hash = self.hash_password(password)
        return user_dao.create(name, password_hash)

    def authenticate(self, name: str, password: str):
        user = user_dao.find_by_name(name.strip())
        if not user:
            return None
        if not self.verify_password(password, user.password_hash):
            return None
        return user
