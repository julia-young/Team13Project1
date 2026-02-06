-- Create Database
CREATE DATABASE IF NOT EXISTS photo_gallery
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_general_ci;

USE photo_gallery;

-- Users
CREATE TABLE IF NOT EXISTS users (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(255) NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_users_username (username),
    UNIQUE KEY uq_users_email (email)
) ENGINE=InnoDB;

-- Photos
CREATE TABLE IF NOT EXISTS photos (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id BIGINT UNSIGNED NOT NULL,
    s3_bucket VARCHAR(63) NOT NULL,
    s3_key VARCHAR(1024) NOT NULL,
    original_name VARCHAR(255) NOT NULL,
    title VARCHAR(120) NULL,
    description TEXT NULL,
    tags VARCHAR(500) NULL,
    content_type VARCHAR(100) NULL,
    size_bytes BIGINT UNSIGNED NULL,
    uploaded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_photos_user_time (user_id, uploaded_at),
    KEY idx_photos_title (title),
    KEY idx_photos_tags (tags),
    CONSTRAINT fk_photos_user
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;