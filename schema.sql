CREATE DATABASE IF NOT EXISTS oshist CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE oshist;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    theme_type VARCHAR(20) NOT NULL DEFAULT 'simple',
    accent_color VARCHAR(7) NOT NULL DEFAULT '#4A90D9',
    background_image_path VARCHAR(255) NULL,
    header_image_path VARCHAR(255) NULL,
    reminder_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS series (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS characters (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    series_id INT NULL,
    name VARCHAR(100) NOT NULL,
    color VARCHAR(7) NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (series_id) REFERENCES series(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS stores (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS brands (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    series_id INT NULL,
    category_id INT NULL,
    name VARCHAR(200) NOT NULL,
    purchase_date DATE NULL,
    price DECIMAL(12, 2) NULL,
    quantity INT NOT NULL DEFAULT 1,
    memo TEXT NULL,
    image_path VARCHAR(255) NULL,
    store_id INT NULL,
    brand_id INT NULL,
    purchase_route_code VARCHAR(30) NULL,
    purchase_url VARCHAR(500) NULL,
    favorite BOOLEAN NOT NULL DEFAULT FALSE,
    expected_delivery_date DATE NULL,
    delivery_status VARCHAR(20) NOT NULL DEFAULT 'delivered',
    delivery_reminder_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    draft_flg BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (series_id) REFERENCES series(id) ON DELETE SET NULL,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL,
    FOREIGN KEY (store_id) REFERENCES stores(id) ON DELETE SET NULL,
    FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE SET NULL,
    CONSTRAINT chk_items_quantity CHECK (quantity >= 1),
    CONSTRAINT chk_items_delivery_status CHECK (
        delivery_status IN ('pending', 'shipped', 'delivered', 'cancelled')
    )
);

CREATE TABLE IF NOT EXISTS tags (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS item_characters (
    item_id INT NOT NULL,
    character_id INT NOT NULL,
    PRIMARY KEY (item_id, character_id),
    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE,
    FOREIGN KEY (character_id) REFERENCES characters(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS item_tags (
    item_id INT NOT NULL,
    tag_id INT NOT NULL,
    PRIMARY KEY (item_id, tag_id),
    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS budgets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    year INT NOT NULL,
    month INT NOT NULL,
    amount DECIMAL(12, 2) NOT NULL,
    target_series_id INT NULL,
    target_character_id INT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (target_series_id) REFERENCES series(id) ON DELETE SET NULL,
    FOREIGN KEY (target_character_id) REFERENCES characters(id) ON DELETE SET NULL,
    CONSTRAINT chk_budgets_amount CHECK (amount > 0),
    CONSTRAINT chk_budgets_month CHECK (month BETWEEN 1 AND 12)
);

CREATE INDEX idx_items_user_date ON items(user_id, purchase_date);
CREATE INDEX idx_items_user_series ON items(user_id, series_id);
CREATE INDEX idx_items_user_category ON items(user_id, category_id);
