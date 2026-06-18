# OshiSt Phase2 Verification on Windows

この手順書は、MySQL 導入後に OshiSt の Phase1 / Phase2 機能を順番に確認するためのものです。ここに書かれた確認は、実行した結果を成功扱いにせず、ユーザーが後で実施して記録する前提です。

## 前提

- Windows 11 を使用します。
- Python 3.12.10、`.venv`、`requirements.txt` のインストールは完了済みです。
- `docs/mysql_setup_windows.md` の手順に沿って MySQL を導入してから、この手順を実施します。
- `.env` は Git 管理対象外、`.env.example` は Git 管理対象です。
- `schema.sql` と `phase2_additional.sql` は、これから適用確認します。
- アップロード設定は `config.py` の `Config.UPLOAD_DIR` です。未設定時の既定値は `C:\Users\m_a_m\Documents\Codex\2026-06-13\github-plugin-github-openai-curated-remote\work\OshiSt\uploads` です。

## 1. 環境・DB・起動確認

このセクションの目的: Python、MySQL、SQL適用、Flask起動までの土台が正しく揃っているか確認します。

### 1. Pythonと仮想環境の確認

何を確認するか: Windows と仮想環境の Python が 3.12 系で動くことを確認します。

```powershell
py --version
python --version
.\.venv\Scripts\python.exe --version
```

成功条件: いずれも Python 3.12 系が表示されます。失敗時は PATH、`.venv` の作成場所、PowerShell の作業ディレクトリを確認します。

### 2. `requirements.txt`の依存関係確認

何を確認するか: Flask と MySQL 接続ライブラリが仮想環境に入っていることを確認します。

```powershell
.\.venv\Scripts\python.exe -m pip show Flask mysql-connector-python python-dotenv bcrypt Werkzeug
```

成功条件: 各パッケージの `Name` と `Version` が表示されます。失敗時は `.\.venv\Scripts\python.exe -m pip install -r requirements.txt` を再実行します。

### 3. MySQLサービス確認

何を確認するか: MySQL Server が Windows サービスとして登録され、起動していることを確認します。

```powershell
Get-Service | Where-Object {
    $_.Name -like '*mysql*' -or
    $_.DisplayName -like '*mysql*'
}
```

成功条件: `MySQL84` または `MySQL80` などが表示され、`Status` が `Running` です。停止中なら管理者 PowerShell で `Start-Service サービス名` を実行します。

### 4. `mysql`コマンド確認

何を確認するか: PowerShell から MySQL クライアントを実行できることを確認します。

```powershell
where.exe mysql
mysql --version
```

PATH にない場合はフルパスで確認します。

```powershell
& "C:\Program Files\MySQL\MySQL Server 8.4\bin\mysql.exe" --version
```

成功条件: MySQL 8.x のバージョンが表示されます。失敗時は `mysql.exe` の場所と PATH 設定を確認します。

### 5. `.env`確認

何を確認するか: Flask が接続に使う環境変数が `.env` に設定されていることを確認します。

```powershell
Select-String -Path .env -Pattern 'FLASK_SECRET_KEY|MYSQL_HOST|MYSQL_PORT|MYSQL_USER|MYSQL_PASSWORD|MYSQL_DATABASE'
git ls-files .env .env.example
```

成功条件: `.env` に必要項目があり、`git ls-files` には `.env.example` だけが表示されます。秘密情報は画面共有やコミットに含めないでください。

### 6. OshiSt用DBとユーザー確認

何を確認するか: `oshist` DB とアプリ専用ユーザーで接続できることを確認します。

```powershell
mysql -u oshist -p -e "SHOW DATABASES;"
```

PATH にない場合:

```powershell
& "C:\Program Files\MySQL\MySQL Server 8.4\bin\mysql.exe" -u oshist -p -e "SHOW DATABASES;"
```

成功条件: `oshist` が表示されます。失敗時はユーザー名、ホスト、パスワード、権限、認証方式を確認します。

### 7. `schema.sql`適用

何を確認するか: Phase1 基本テーブルを作成できることを確認します。

```powershell
Get-Content -Raw schema.sql |
    mysql -u root -p
```

PATH にない場合:

```powershell
Get-Content -Raw schema.sql |
    & "C:\Program Files\MySQL\MySQL Server 8.4\bin\mysql.exe" -u root -p
```

成功条件: エラーなく終了します。失敗時は `Access denied`、`Unknown database`、文字コード、既存テーブルの状態を確認します。

### 8. `phase2_additional.sql`の事前確認

何を確認するか: 一意制約や `NOT NULL` 変更前に、既存データの重複とNULLを確認します。

```powershell
mysql -u root -p oshist
```

MySQL内で `phase2_additional.sql` 先頭の重複確認 `SELECT` と `characters WHERE series_id IS NULL` を先に実行します。

成功条件: すべて0件です。1件でも出た場合は、ALTER や CALL を続行せず、対象データを修正してから再確認します。

### 9. `phase2_additional.sql`適用

何を確認するか: Phase2 の一意制約、外部キー、検索用インデックスを追加できることを確認します。

```powershell
Get-Content -Raw phase2_additional.sql |
    mysql -u root -p
```

PATH にない場合:

```powershell
Get-Content -Raw phase2_additional.sql |
    & "C:\Program Files\MySQL\MySQL Server 8.4\bin\mysql.exe" -u root -p
```

成功条件: エラーなく終了します。失敗時は直前の事前確認結果、外部キー、重複データを確認します。

### 10. テーブル・制約・インデックス確認

何を確認するか: Phase2で必要なテーブル、制約、インデックスが存在することを確認します。

```powershell
mysql -u root -p oshist -e "SHOW TABLES; SHOW CREATE TABLE items; SHOW CREATE TABLE characters; SHOW INDEX FROM items; SHOW INDEX FROM item_characters;"
```

成功条件: `series`, `categories`, `characters`, `items`, `item_characters` があり、配送検索用・キャラ検索用インデックスが確認できます。

### 11. `create_app()`確認

何を確認するか: Flaskアプリが設定とBlueprintを読み込めることを確認します。

```powershell
.\.venv\Scripts\python.exe -m compileall .
.\.venv\Scripts\python.exe -c "from oshist import create_app; app = create_app(); print(app.url_map)"
```

成功条件: 例外が出ず、`items`, `masters`, `delivery`, `budget`, `auth` などのURLが表示されます。

### 12. Flask起動

何を確認するか: ローカルでWebアプリが起動することを確認します。

```powershell
.\.venv\Scripts\python.exe run.py
```

成功条件: `http://127.0.0.1:5000` などで待ち受けます。失敗時は `.env`、MySQLサービス、ポート競合、Python例外を確認します。

## 2. 認証確認

このセクションの目的: ログイン前後の基本動作とセッション管理が正しく働くか確認します。

### 13. ログイン画面表示

何を確認するか: 未ログインでログイン画面を表示できることを確認します。

ブラウザで `http://127.0.0.1:5000/login` を開きます。

成功条件: ログインフォームが表示されます。失敗時は Flask の端末ログ、テンプレートエラー、DB接続エラーを確認します。

### 14. 新規登録

何を確認するか: 確認用ユーザーを作成できることを確認します。

`user_a` と `user_b` を作成します。実際のパスワードは手順書やコミットに残さず、自分で安全な値を設定してください。

成功条件: 登録後にログイン画面またはホームへ進めます。失敗時は重複ユーザー名、CSRF、DB接続を確認します。

### 15. ログイン

何を確認するか: 登録したユーザーでログインできることを確認します。

`user_a` でログインし、ホーム画面へ遷移します。

成功条件: ナビゲーションとログアウトボタンが表示されます。失敗時はユーザー名、パスワード、セッションCookieを確認します。

### 16. ログアウト

何を確認するか: セッションを破棄してログアウトできることを確認します。

画面のログアウト操作を実行します。

成功条件: ログイン画面に戻り、ログイン必須ページへ直接アクセスするとログイン画面へ戻されます。

### 17. 未ログイン時アクセス制御

何を確認するか: 未ログインで保護ページを開けないことを確認します。

ログアウト後、`/items/`, `/masters/series`, `/masters/categories`, `/masters/characters`, `/delivery/`, `/budget/` を直接開きます。

成功条件: `/login` へリダイレクトされます。500エラーの場合は `login_required`、セッション、Blueprint登録を確認します。

### 18. セッションタイムアウト設定確認

何を確認するか: セッション有効期限が30分設定であることを確認します。

```powershell
Select-String -Path config.py -Pattern 'PERMANENT_SESSION_LIFETIME'
.\.venv\Scripts\python.exe -c "from oshist import create_app; app=create_app(); print(app.permanent_session_lifetime)"
```

成功条件: `1800` 秒、または `0:30:00` が確認できます。実際に30分待つ確認は手動確認として記録します。

## 3. Phase1・Phase2機能確認

このセクションの目的: ログイン後の主要機能、所有者チェック、検索、配送、画像処理が期待どおり動くか確認します。

### 19. 2ユーザーによる所有者チェック

何を確認するか: 他ユーザーのデータを閲覧・更新・削除・紐付けできないことを確認します。

`user_a` でシリーズ、カテゴリ、キャラ、アイテムを登録し、`user_b` でも別データを登録します。IDは一覧画面のURLやDB確認で控えます。

`user_a` ログイン中に `user_b` のシリーズID、カテゴリID、キャラID、アイテムIDをURLやPOSTで直接指定します。

成功条件: 403、404、入力エラー、または一覧へ戻るなどで拒否され、500エラーや他ユーザーデータ表示になりません。

### 20. シリーズ管理CRUD

何を確認するか: ユーザーごとのシリーズ一覧、登録、編集、削除制御を確認します。

シリーズを登録、同名登録、編集、未使用シリーズ削除、使用中シリーズ削除の順に試します。

成功条件: 同一ユーザー内の同名は拒否され、アイテムやキャラで使用中のシリーズは削除できません。

### 21. カテゴリ管理CRUD

何を確認するか: ユーザーごとのカテゴリ一覧、登録、編集、削除制御を確認します。

カテゴリを登録、同名登録、編集、未使用カテゴリ削除、アイテム使用中カテゴリ削除の順に試します。

成功条件: 同一ユーザー内の同名は拒否され、アイテムで使用中のカテゴリは削除できません。

### 22. キャラ管理CRUD

何を確認するか: キャラが必ずシリーズに紐づき、推しカラーと削除制御が動くことを確認します。

シリーズを選んでキャラを登録し、同一シリーズ内の同名、別シリーズの同名、編集、使用中キャラ削除を試します。

成功条件: 同一ユーザー・同一シリーズ内の同名は拒否され、アイテムで使用中のキャラは削除できません。

### 23. アイテム登録

何を確認するか: シリーズ、カテゴリ、複数キャラ、価格、数量、URL、配送情報を保存できることを確認します。

数量未入力、数量1以上、価格空欄、`http` / `https` URL、購入店、ブランド相当の入力欄を試します。

成功条件: 正常値は保存され、数量0、負数、不正ID、`javascript:` や `data:` URL は拒否されます。

### 24. アイテム編集

何を確認するか: 登録済みアイテムを安全に更新できることを確認します。

名前、シリーズ、カテゴリ、キャラ、数量、価格、URL、配送予定日を変更します。

成功条件: 自分のアイテムだけ更新でき、他ユーザーIDや不正値は拒否されます。

### 25. 下書き保存

何を確認するか: 下書き状態で保存できることを確認します。

必須項目を最小限にして下書き保存し、一覧と検索での表示を確認します。

成功条件: 下書きは通常検索では非表示で、「下書きを含む」を指定した場合のみ表示されます。

### 26. 正式登録

何を確認するか: 正式登録済みアイテムとして一覧・詳細・予算計算対象になることを確認します。

下書きを正式登録へ変更、または新規で正式登録します。

成功条件: 一覧に表示され、詳細画面でシリーズ、カテゴリ、キャラ、配送情報が確認できます。

### 27. 複数キャラ保存

何を確認するか: アイテムとキャラの多対多保存ができることを確認します。

1つのアイテムに複数キャラを選択して保存し、詳細と検索結果を確認します。

成功条件: 複数キャラ名が表示され、キャラ検索しても同じアイテムが重複表示されません。

### 28. 検索機能

何を確認するか: 正式登録を基本に、複数条件のAND検索が動くことを確認します。

アイテム名、シリーズ、カテゴリ、キャラ、配送ステータスを単独・複数条件で検索します。

成功条件: デフォルトで下書き非表示、「下書きを含む」で表示、複数条件はAND、キャラJOINで重複表示なしです。

### 29. 配送管理

何を確認するか: 配送ステータス、予定日、リマインドON/OFFを更新できることを確認します。

`pending`, `shipped`, `delivered`, `cancelled` を順に設定し、配送予定日とリマインドを変更します。

成功条件: 許可ステータスのみ保存され、不正ステータスをPOSTした場合は拒否されます。

### 30. 予算管理

何を確認するか: 月別予算と使用額が正式登録アイテムに基づいて表示されることを確認します。

当月予算を登録し、正式登録アイテムの価格・数量を変更します。

成功条件: 予算額、使用額、残額が期待どおり変化します。下書きやキャンセル配送の扱いも確認します。

### 31. 画像アップロード

何を確認するか: 許可形式の画像だけ保存・表示できることを確認します。

`Config.UPLOAD_DIR` の実使用パスを確認します。

```powershell
.\.venv\Scripts\python.exe -c "from config import Config; print(Config.UPLOAD_DIR)"
Get-ChildItem "C:\Users\m_a_m\Documents\Codex\2026-06-13\github-plugin-github-openai-curated-remote\work\OshiSt\uploads"
```

JPEG、PNG、WEBPをアップロードし、不正形式のファイルも試します。成功条件は許可形式だけ保存され、不正形式が拒否されることです。

### 32. 画像差し替え

何を確認するか: アイテム編集時に画像を差し替えられることを確認します。

差し替え前後でファイル一覧を比較します。

```powershell
Get-ChildItem "C:\Users\m_a_m\Documents\Codex\2026-06-13\github-plugin-github-openai-curated-remote\work\OshiSt\uploads" | Select-Object Name,Length,LastWriteTime
```

成功条件: 詳細画面の画像が新しい画像に変わります。旧画像が残る場合は孤立ファイルとして記録します。

### 33. アイテム削除時の画像確認

何を確認するか: アイテム削除後に画像ファイルが孤立しないか確認します。

現状の画面・Routeにアイテム削除機能がない場合、この項目は「未確認/削除機能なし」と記録します。

削除機能が実装されている場合は、削除前後で `Config.UPLOAD_DIR` のファイル一覧を比較します。

### 34. エラー発生時のログ確認

何を確認するか: 失敗時に原因を追えることを確認します。

Flaskを起動しているPowerShell、ブラウザの表示、MySQLエラー、ネットワークタブを確認します。

成功条件: 500エラー時に端末ログへ例外が出て、入力エラー時は画面に分かりやすいメッセージが表示されます。

## 4. 確認結果の記録

このセクションの目的: 確認結果を機能単位で簡潔に記録し、失敗時の再確認まで追跡します。

### 表1：環境・DB・起動確認

| 確認項目 | 結果 | 成功 / 失敗 / 未確認 | エラーメッセージ | 修正内容 | 再確認結果 |
|---|---|---|---|---|---|
| Python / 仮想環境 / 依存関係 |  |  |  |  |  |
| MySQLサービス / mysqlコマンド |  |  |  |  |  |
| `.env` / DBユーザー / 権限 |  |  |  |  |  |
| `schema.sql` 適用 |  |  |  |  |  |
| `phase2_additional.sql` 事前確認・適用 |  |  |  |  |  |
| テーブル・制約・インデックス |  |  |  |  |  |
| `create_app()` / Flask起動 |  |  |  |  |  |

### 表2：認証確認

| 確認項目 | 結果 | 成功 / 失敗 / 未確認 | エラーメッセージ | 修正内容 | 再確認結果 |
|---|---|---|---|---|---|
| ログイン画面 / 新規登録 |  |  |  |  |  |
| ログイン / ログアウト |  |  |  |  |  |
| 未ログイン時アクセス制御 |  |  |  |  |  |
| セッションタイムアウト設定 |  |  |  |  |  |
| 30分経過後の手動確認 |  |  |  |  |  |

### 表3：機能確認

| 確認項目 | 結果 | 成功 / 失敗 / 未確認 | エラーメッセージ | 修正内容 | 再確認結果 |
|---|---|---|---|---|---|
| 2ユーザー所有者チェック |  |  |  |  |  |
| シリーズ管理CRUD |  |  |  |  |  |
| カテゴリ管理CRUD |  |  |  |  |  |
| キャラ管理CRUD |  |  |  |  |  |
| アイテム登録・編集・下書き・正式登録 |  |  |  |  |  |
| 複数キャラ保存 / 検索 |  |  |  |  |  |
| 配送管理 |  |  |  |  |  |
| 予算管理 |  |  |  |  |  |
| 画像アップロード・差し替え・削除時確認 |  |  |  |  |  |
| エラー発生時のログ確認 |  |  |  |  |  |
