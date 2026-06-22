USE oshist;

-- Remove the obsolete manually entered barcode index when it still exists.
SET @barcode_index_exists = (
    SELECT COUNT(*)
    FROM information_schema.statistics
    WHERE table_schema = DATABASE()
      AND table_name = 'items'
      AND index_name = 'idx_items_user_barcode'
);
SET @sql = IF(
    @barcode_index_exists > 0,
    'ALTER TABLE `items` DROP INDEX `idx_items_user_barcode`',
    'SELECT ''idx_items_user_barcode is already absent'' AS message'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Remove the obsolete manually entered barcode column when it still exists.
SET @barcode_column_exists = (
    SELECT COUNT(*)
    FROM information_schema.columns
    WHERE table_schema = DATABASE()
      AND table_name = 'items'
      AND column_name = 'barcode'
);
SET @sql = IF(
    @barcode_column_exists > 0,
    'ALTER TABLE `items` DROP COLUMN `barcode`',
    'SELECT ''items.barcode is already absent'' AS message'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
