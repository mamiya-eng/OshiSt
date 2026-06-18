# Fix OshiSt MySQL User on Windows

この手順は、`Access denied for user 'oshist'@'localhost'` を安全に確認・修正するためのものです。Codexからroot接続やパスワード入力は実行せず、ユーザーが自分のPowerShellまたはMySQL Workbenchで手動実行します。

## 1. rootでMySQLを開く

PowerShellを開き、次のコマンドを自分で実行します。rootパスワードは画面で対話入力し、ファイルやチャットには書かないでください。

```powershell
& "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -p
```

MySQL Workbenchを使う場合も、rootまたは同等の管理権限ユーザーで接続します。

## 2. 先に確認SQLを実行する

MySQLに入ったら、`docs/check_mysql_user.sql` の内容を先に実行します。これは確認だけで、DBやユーザーを変更しません。

`SHOW GRANTS FOR 'oshist'@'localhost';` は、ユーザーが存在しない場合に失敗します。その場合は結果を見てケースAまたはケースCに分類します。

`oshist` DBに既存テーブルがあっても削除・変更しないでください。

## 3. 結果をケースAからEへ分類する

ケースA: `mysql.user` に `oshist` が1件もない。
ケースB: `'oshist'@'localhost'` は存在するが、アプリやmysql.exe接続がAccess deniedになる。
ケースC: `oshist` は存在するが、Host が `localhost` ではない。
ケースD: `'oshist'@'localhost'` の `account_locked` が `Y`。
ケースE: ユーザーは存在し、ログインできるが、`oshist.*` への権限が不足している。

## 4. 必要なSQLだけ実行する

`docs/fix_mysql_user.sql` を開き、自分のケースに合う部分だけ実行します。ファイル全体を何も考えずに一括実行しないでください。

`REPLACE_WITH_SECURE_PASSWORD` は、自分で決めた安全なパスワードに置き換えます。同じ値を `.env` の `MYSQL_PASSWORD` に設定します。

既存ユーザー削除、既存DB削除、既存テーブル削除は行いません。

## 5. 権限を確認する

修正後、次を実行して `oshist.*` への権限があることを確認します。

```sql
SHOW GRANTS FOR 'oshist'@'localhost';
```

`GRANT ALL PRIVILEGES ON *.*` は使わないでください。OshiStでは `oshist.*` の範囲だけにします。

## 6. 認証方式について

MySQL 8.0の標準認証方式は `caching_sha2_password` です。`mysql-connector-python==9.2.0` は通常この方式に対応します。

`mysql_native_password` へ変更するとセキュリティが下がる可能性があります。まずはユーザー名、Host、パスワード、権限、ロック状態を確認してください。

認証方式の変更が必要な場合は、明示承認後の別タスクで扱います。この手順では `mysql_native_password` への変更SQLは作成しません。

## 7. mysql.exeで接続確認する

SQL修正後、PowerShellで次を手動実行します。パスワードは対話入力します。

```powershell
& "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" `
    -u oshist `
    -p `
    -h localhost `
    -P 3306 `
    -D oshist
```

成功条件は、`oshist` DBへ接続できることです。

## 8. Pythonから接続確認する

同じパスワードを `.env` の `MYSQL_PASSWORD` に設定した後、次を実行します。

```powershell
.\.venv\Scripts\python.exe test_db_connection.py
```

成功条件は、`DB connection OK` だけが表示されることです。

## 9. 次へ進む条件

mysql.exe接続とPython接続の両方が成功したら、次の別タスクで `schema.sql` 適用へ進みます。

どちらかが失敗する場合は、エラー内容を確認し、Host、ユーザー名、パスワード、DB名、権限、アカウントロックを再確認します。
