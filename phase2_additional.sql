USE oshist;

-- Phase2 additional SQL.
-- This file assumes the base tables from schema.sql already exist.
-- Run the pre-check SELECT statements first. If any rows are returned,
-- fix duplicate or NULL data before running the ALTER/CALL statements.

-- 1. Pre-check duplicate data before adding unique keys.
SELECT user_id, name, COUNT(*) AS duplicate_count
FROM series
GROUP BY user_id, name
HAVING COUNT(*) > 1;

SELECT user_id, name, COUNT(*) AS duplicate_count
FROM categories
GROUP BY user_id, name
HAVING COUNT(*) > 1;

SELECT user_id, series_id, name, COUNT(*) AS duplicate_count
FROM characters
GROUP BY user_id, series_id, name
HAVING COUNT(*) > 1;

SELECT user_id, name, COUNT(*) AS duplicate_count
FROM stores
GROUP BY user_id, name
HAVING COUNT(*) > 1;

-- 2. Characters must belong to a series in Phase2.
SELECT id, user_id, name
FROM characters
WHERE series_id IS NULL;

-- 3. Use RESTRICT for master data that must not be deleted while in use.
-- schema.sql originally uses ON DELETE SET NULL for these relationships.
-- Phase2 also checks this in the Service layer, but DB-level RESTRICT
-- protects direct SQL deletes as well.

DELIMITER //

DROP PROCEDURE IF EXISTS add_unique_if_missing//
CREATE PROCEDURE add_unique_if_missing(
    IN p_table_name VARCHAR(64),
    IN p_index_name VARCHAR(64),
    IN p_index_columns VARCHAR(255)
)
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.statistics
        WHERE table_schema = DATABASE()
          AND table_name = p_table_name
          AND index_name = p_index_name
    ) THEN
        SET @sql = CONCAT(
            'ALTER TABLE `', p_table_name, '` ADD UNIQUE KEY `',
            p_index_name, '` (', p_index_columns, ')'
        );
        PREPARE stmt FROM @sql;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;
    END IF;
END//

DROP PROCEDURE IF EXISTS add_index_if_missing//
CREATE PROCEDURE add_index_if_missing(
    IN p_table_name VARCHAR(64),
    IN p_index_name VARCHAR(64),
    IN p_index_columns VARCHAR(255)
)
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.statistics
        WHERE table_schema = DATABASE()
          AND table_name = p_table_name
          AND index_name = p_index_name
    ) THEN
        SET @sql = CONCAT(
            'CREATE INDEX `', p_index_name, '` ON `',
            p_table_name, '` (', p_index_columns, ')'
        );
        PREPARE stmt FROM @sql;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;
    END IF;
END//

DROP PROCEDURE IF EXISTS drop_fk_by_column//
CREATE PROCEDURE drop_fk_by_column(
    IN p_table_name VARCHAR(64),
    IN p_column_name VARCHAR(64),
    IN p_referenced_table_name VARCHAR(64)
)
BEGIN
    SET @fk_name = NULL;
    SELECT kcu.constraint_name
      INTO @fk_name
      FROM information_schema.key_column_usage kcu
     WHERE kcu.table_schema = DATABASE()
       AND kcu.table_name = p_table_name
       AND kcu.column_name = p_column_name
       AND kcu.referenced_table_name = p_referenced_table_name
     LIMIT 1;

    IF @fk_name IS NOT NULL THEN
        SET @sql = CONCAT(
            'ALTER TABLE `', p_table_name, '` DROP FOREIGN KEY `', @fk_name, '`'
        );
        PREPARE stmt FROM @sql;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;
        SET @fk_name = NULL;
    END IF;
END//

DROP PROCEDURE IF EXISTS add_fk_if_missing//
CREATE PROCEDURE add_fk_if_missing(
    IN p_table_name VARCHAR(64),
    IN p_constraint_name VARCHAR(64),
    IN p_column_name VARCHAR(64),
    IN p_referenced_table_name VARCHAR(64),
    IN p_referenced_column_name VARCHAR(64),
    IN p_on_delete VARCHAR(20)
)
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.table_constraints
        WHERE table_schema = DATABASE()
          AND table_name = p_table_name
          AND constraint_name = p_constraint_name
          AND constraint_type = 'FOREIGN KEY'
    ) THEN
        SET @sql = CONCAT(
            'ALTER TABLE `', p_table_name, '` ADD CONSTRAINT `',
            p_constraint_name, '` FOREIGN KEY (`', p_column_name,
            '`) REFERENCES `', p_referenced_table_name, '` (`',
            p_referenced_column_name, '`) ON DELETE ', p_on_delete
        );
        PREPARE stmt FROM @sql;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;
    END IF;
END//

DELIMITER ;

-- 4. Unique keys.
CALL add_unique_if_missing('series', 'uq_series_user_name', '`user_id`, `name`');
CALL add_unique_if_missing('categories', 'uq_categories_user_name', '`user_id`, `name`');
CALL add_unique_if_missing('characters', 'uq_characters_user_series_name', '`user_id`, `series_id`, `name`');
CALL add_unique_if_missing('stores', 'uq_stores_user_name', '`user_id`, `name`');

-- 5. Foreign key delete behavior.
-- series/categories/characters cannot be deleted while items use them.
CALL drop_fk_by_column('items', 'series_id', 'series');
CALL add_fk_if_missing('items', 'fk_items_series_restrict', 'series_id', 'series', 'id', 'RESTRICT');

CALL drop_fk_by_column('items', 'category_id', 'categories');
CALL add_fk_if_missing('items', 'fk_items_category_restrict', 'category_id', 'categories', 'id', 'RESTRICT');

CALL drop_fk_by_column('characters', 'series_id', 'series');
ALTER TABLE characters
    MODIFY series_id INT NOT NULL;
CALL add_fk_if_missing('characters', 'fk_characters_series_restrict', 'series_id', 'series', 'id', 'RESTRICT');

-- item_characters is a junction table. Its existing CASCADE behavior removes
-- only junction rows when an item/character is deleted. The Phase2 UI blocks
-- deleting characters that are still used by items.

-- 6. Search indexes.
CALL add_index_if_missing('items', 'idx_items_user_delivery', '`user_id`, `delivery_status`, `expected_delivery_date`');
CALL add_index_if_missing('characters', 'idx_characters_user_series', '`user_id`, `series_id`');
CALL add_index_if_missing('item_characters', 'idx_item_characters_character', '`character_id`, `item_id`');

DROP PROCEDURE IF EXISTS add_unique_if_missing;
DROP PROCEDURE IF EXISTS add_index_if_missing;
DROP PROCEDURE IF EXISTS drop_fk_by_column;
DROP PROCEDURE IF EXISTS add_fk_if_missing;
