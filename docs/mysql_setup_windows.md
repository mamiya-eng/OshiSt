# OshiSt Windows MySQL Setup

この手順書は、Windows 11 上で OshiSt 用の MySQL 環境を用意するためのものです。ここではインストールや SQL 適用を実行せず、ユーザー自身が安全に作業できる手順をまとめます。

## 前提条件

- Windows 11 を使用します。
- OshiSt は `Python 3.12.10`、`.venv`、`requirements.txt` のインストールまで完了している前提です。
- `.env` は Git 管理対象外、`.env.example` は Git 管理対象です。
- MySQL Server、MySQL Workbench、Docker は未導入の前提で説明します。

## 1. MySQL 関連ツールの違い

MySQL Server はデータを保存して処理する本体です。OshiSt が接続する先は MySQL Server です。

MySQL Workbench は画面操作用の管理ツールです。便利ですが、Workbench だけでは Flask アプリ用のDBサーバーにはなりません。

`mysql` コマンドは PowerShell から SQL を実行するクライアントです。`schema.sql` と `phase2_additional.sql` の適用に使います。

## 2. `mysql-connector-python` との違い

`mysql-connector-python` は Python から MySQL Server へ接続するためのライブラリです。OshiSt の `requirements.txt` に含まれています。

このライブラリを入れても MySQL Server はインストールされません。DB本体は別途 MySQL Community Server を入れる必要があります。

## 3. 推奨構成

OshiSt では MySQL Community Server 8.4 を第一候補にします。MySQL 8.0 も、既存SQLの範囲では大きな互換性問題は見つかっていません。

新規構築では、MySQL Server、mysql コマンド、必要に応じて MySQL Workbench を導入します。Docker はこの手順では使いません。

## 4. MySQL Community Server 8.x の導入

公式サイトから MySQL Installer for Windows をダウンロードします。配布元が公式であることを確認してください。

Installer では、最小構成なら MySQL Server と MySQL Shell または MySQL Client Programs を選びます。画面で操作したい場合だけ Workbench も追加します。

迷った場合は Developer Default ではなく Custom を選ぶと、余計な製品を避けやすくなります。

## 5. Installer の主な選択項目

Server Configuration では、Standalone MySQL Server を選びます。ポートは通常 `3306` のままで構いません。

Authentication Method は、原則として MySQL のデフォルトを使います。古いクライアント互換のために安易に変更しないでください。

Windows Service は有効にします。サービス名は `MySQL84` または `MySQL80` のような名前になることが多いです。

## 6. root パスワードの設定と保管

root パスワードは推測されにくい値にしてください。手順書、README、Git管理ファイルには書かないでください。

パスワード管理ツールなどに保管し、紛失しないようにします。root は管理用で、OshiSt の通常接続には専用ユーザーを使います。

## 7. Windows サービス名の確認

MySQL を入れた後、PowerShell でサービス名を確認します。

```powershell
Get-Service | Where-Object {
    $_.Name -like '*mysql*' -or
    $_.DisplayName -like '*mysql*'
}
```

`Status` が `Running` なら起動中です。`Stopped` ならサービスはありますが停止しています。

## 8. MySQL サービスの起動・停止

サービス名が `MySQL84` の場合の例です。実際のサービス名に置き換えてください。

```powershell
Start-Service MySQL84
Stop-Service MySQL84
Restart-Service MySQL84
```

管理者権限の PowerShell が必要な場合があります。サービス停止中は Flask からDB接続できません。

## 9. `mysql.exe` の場所確認

代表的な場所を確認します。インストール先により `8.4` または `8.0` が変わります。

```powershell
Test-Path "C:\Program Files\MySQL\MySQL Server 8.4\bin\mysql.exe"
Test-Path "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe"
```

PATH に入っているかは次で確認します。

```powershell
where.exe mysql
Get-Command mysql -ErrorAction SilentlyContinue
```

## 10. PATH に追加しない場合

PATH に追加しない場合は、`mysql.exe` をフルパスで実行します。

```powershell
& "C:\Program Files\MySQL\MySQL Server 8.4\bin\mysql.exe" -u root -p
```

`&` は、空白を含むパスの実行に必要です。

## 11. OshiSt 用DBを作成する

root で MySQL にログインして、OshiSt 用DBを作成します。

```sql
CREATE DATABASE IF NOT EXISTS oshist
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;
```

`utf8mb4` は絵文字や日本語を安全に扱うために使います。

## 12. OshiSt 用ユーザーを作成する

アプリ専用ユーザーを作成します。実際のパスワードは自分で決めた安全な値に置き換えてください。

```sql
CREATE USER IF NOT EXISTS 'oshist'@'localhost'
    IDENTIFIED BY 'ユーザーが自分で設定する安全なパスワード';
```

root ユーザーを Flask アプリから使わないようにします。

## 13. 権限付与

OshiSt 用DBだけに権限を付与します。

```sql
GRANT ALL PRIVILEGES ON oshist.* TO 'oshist'@'localhost';
FLUSH PRIVILEGES;
```

別DBへの権限は不要です。必要最小限の範囲に閉じます。

## 14. `.env` の設定例

`.env.example` を参考に、Git管理対象外の `.env` を作成します。値はダミーではなく、自分の環境に合わせます。

```env
FLASK_SECRET_KEY=replace-with-random-secret
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=oshist
MYSQL_PASSWORD=replace-with-your-password
MYSQL_DATABASE=oshist
```

`.env` は Git に追加しないでください。

## 15. `schema.sql` の適用

PowerShell では `<` の扱いでつまずくことがあるため、`Get-Content -Raw` を優先します。

```powershell
Get-Content -Raw schema.sql |
    mysql -u root -p
```

PATH にない場合はフルパスで実行します。

```powershell
Get-Content -Raw schema.sql |
    & "C:\Program Files\MySQL\MySQL Server 8.4\bin\mysql.exe" -u root -p
```

## 16. `phase2_additional.sql` の事前確認

追加SQLの先頭にある重複確認 `SELECT` を先に確認します。結果が0件であることを確認してから、ALTER や CALL に進みます。

特に `characters.series_id IS NULL` が0件であることを確認してください。NULL が残っていると、`series_id` を `NOT NULL` に変更できません。

問題がある場合は、追加SQLの続きは実行せず、データ修正方針を決めてから再開します。

## 17. 追加SQLの適用

事前確認が問題なければ、追加SQLを適用します。

```powershell
Get-Content -Raw phase2_additional.sql |
    mysql -u root -p
```

PATH にない場合の例です。

```powershell
Get-Content -Raw phase2_additional.sql |
    & "C:\Program Files\MySQL\MySQL Server 8.4\bin\mysql.exe" -u root -p
```

このSQLには、同じ一意制約やインデックスを重複作成しないためのストアドプロシージャが含まれています。

## 18. テーブル・制約・インデックス確認

適用後にテーブル一覧を確認します。

```sql
USE oshist;
SHOW TABLES;
```

制約とインデックスは次で確認します。

```sql
SHOW CREATE TABLE items\G
SHOW CREATE TABLE characters\G
SHOW INDEX FROM items;
SHOW INDEX FROM item_characters;
```

## 19. Flask アプリからの接続確認

`.env` を設定した後、仮想環境の Python でアプリ作成を確認します。

```powershell
.\.venv\Scripts\python.exe -c "from oshist import create_app; app = create_app(); print(app.url_map)"
```

DB接続を伴う画面は、MySQLサービス起動後にブラウザからログインして確認します。

## 20. 認証方式の注意

MySQL 8.x の新規構築では、原則としてデフォルト認証方式を使います。`caching_sha2_password` は MySQL 8系で一般的な認証方式です。

`mysql_native_password` は古いクライアント互換で使われることがありますが、標準手順として変更を推奨しません。

`mysql-connector-python==9.2.0` から接続できない場合は、ユーザー名、ホスト、パスワード、権限、認証方式を順に確認します。

## 21. よくあるエラーと対処

### `mysql` が認識されない

PATH に `mysql.exe` が入っていません。`where.exe mysql` で確認し、PATHに追加するかフルパスで実行します。

### MySQLサービスが起動していない

`Get-Service` で `Status` を確認します。停止中なら `Start-Service MySQL84` のように起動します。

### Access denied

ユーザー名、ホスト、パスワード、権限、認証方式を確認します。`.env` の `MYSQL_USER` と `MYSQL_PASSWORD` も見直します。

### Unknown database

`MYSQL_DATABASE` に指定したDBがありません。`CREATE DATABASE IF NOT EXISTS oshist ...` を実行したか確認します。

### Table already exists

`schema.sql` は `CREATE TABLE IF NOT EXISTS` を使っています。別名の既存テーブルや途中失敗がないか確認します。

### Duplicate entry

一意制約追加時に既存データが重複しています。`phase2_additional.sql` 先頭の重複確認SQLで対象を特定します。

### Cannot add foreign key constraint

参照先データがない、型が一致しない、NULL禁止にできないなどが原因です。特に `characters.series_id IS NULL` を確認します。

### Communications link failure

MySQLサービス停止、ポート違い、3306競合、ファイアウォールなどを確認します。`MYSQL_HOST` と `MYSQL_PORT` も確認します。

### `.env` の接続情報不一致

DB名、ユーザー名、パスワード、ポートが MySQL 側の設定と一致しているか確認します。`.env.example` ではなく `.env` を使います。

### 文字コード問題

DBが `utf8mb4` で作られているか確認します。日本語や絵文字を扱うため、`utf8mb4_unicode_ci` を使います。

### 3306ポート競合

別のDBや古いMySQLが3306を使っている可能性があります。MySQL Installer の設定やサービス一覧を確認します。

### 認証プラグイン関連エラー

古いクライアントや設定変更が原因の場合があります。まず `mysql-connector-python` のバージョン、ユーザーの認証方式、権限を確認します。

### MySQL 8.0 と 8.4 の設定差

Installer の画面やデフォルト設定が異なる場合があります。OshiSt のSQLは8.x向けですが、未確認の設定差を対応済みとは断定しないでください。

## 参考: SQL互換性の静的確認メモ

`schema.sql` は `CREATE DATABASE`, `CREATE TABLE IF NOT EXISTS`, `CHECK`, `FOREIGN KEY`, `CREATE INDEX` を使っています。MySQL 8.0/8.4 で一般的に使える構文です。

`phase2_additional.sql` は `DELIMITER`, ストアドプロシージャ、`information_schema`, `PREPARE/EXECUTE`, `ALTER TABLE` を使います。mysql コマンドで実行する前提です。

`phase2_additional.sql` は既存データの状態によって失敗します。事前確認で問題がないことを確認してから適用してください。
