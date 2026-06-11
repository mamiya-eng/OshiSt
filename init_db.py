"""データベース初期化スクリプト。MySQL が起動している必要があります。"""
import sys
from pathlib import Path

import mysql.connector

from config import Config

SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def main():
    sql = SCHEMA_PATH.read_text(encoding="utf-8")
    statements = [
        s.strip()
        for s in sql.split(";")
        if s.strip() and not s.strip().startswith("--")
    ]

    conn = mysql.connector.connect(
        host=Config.MYSQL_HOST,
        port=Config.MYSQL_PORT,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
    )
    cursor = conn.cursor()

    for statement in statements:
        cursor.execute(statement)

    conn.commit()
    cursor.close()
    conn.close()
    print("データベースの初期化が完了しました。")


if __name__ == "__main__":
    try:
        main()
    except mysql.connector.Error as exc:
        print(f"エラー: {exc}", file=sys.stderr)
        sys.exit(1)
