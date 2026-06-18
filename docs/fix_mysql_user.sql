-- OshiSt MySQL user fix SQL template.
-- Run this manually as root only after checking docs/check_mysql_user.sql.
-- Do not run this whole file blindly. Pick only the section that matches your case.
-- Replace REPLACE_WITH_SECURE_PASSWORD with the password you will also put in .env.
-- Do not commit the real password to Git.

-- Common: create the OshiSt database if it does not exist.
-- This does not delete or modify existing tables.
CREATE DATABASE IF NOT EXISTS oshist
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

-- Case A: the oshist user does not exist at all.
-- Use this when docs/check_mysql_user.sql returns no rows for User = 'oshist'.
CREATE USER IF NOT EXISTS 'oshist'@'localhost'
    IDENTIFIED BY 'REPLACE_WITH_SECURE_PASSWORD';

GRANT ALL PRIVILEGES ON oshist.* TO 'oshist'@'localhost';

-- Case B: 'oshist'@'localhost' exists, but the password does not match .env.
-- Use this when the user exists but Python or mysql.exe reports Access denied.
ALTER USER 'oshist'@'localhost'
    IDENTIFIED BY 'REPLACE_WITH_SECURE_PASSWORD';

-- Case C: an oshist user exists for another Host, but not for localhost.
-- Use this when mysql.user shows oshist with a Host other than localhost.
CREATE USER IF NOT EXISTS 'oshist'@'localhost'
    IDENTIFIED BY 'REPLACE_WITH_SECURE_PASSWORD';

GRANT ALL PRIVILEGES ON oshist.* TO 'oshist'@'localhost';

-- Case D: 'oshist'@'localhost' exists but account_locked is Y.
-- Use this only when mysql.user shows account_locked = Y.
ALTER USER 'oshist'@'localhost'
    ACCOUNT UNLOCK;

-- Case E: 'oshist'@'localhost' exists, password works, but grants are missing.
-- Use this when SHOW GRANTS does not include privileges on oshist.*.
GRANT ALL PRIVILEGES ON oshist.* TO 'oshist'@'localhost';

-- Run after the chosen case section.
FLUSH PRIVILEGES;

SHOW GRANTS FOR 'oshist'@'localhost';
