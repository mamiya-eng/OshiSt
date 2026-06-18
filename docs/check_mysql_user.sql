-- OshiSt MySQL user check SQL.
-- Run this manually as a MySQL administrative user such as root.
-- This file only checks users, database existence, grants, and tables.
-- It does not create, update, or delete any data.

SELECT
    User,
    Host,
    plugin,
    account_locked
FROM mysql.user
WHERE User = 'oshist';

SHOW DATABASES LIKE 'oshist';

-- This statement fails if 'oshist'@'localhost' does not exist.
-- If it fails, classify the result as Case A or Case C in fix_mysql_user_windows.md.
SHOW GRANTS FOR 'oshist'@'localhost';

-- Run these statements only when the oshist database exists.
-- They are read-only checks. Do not drop or modify existing tables.
USE oshist;
SHOW TABLES;
