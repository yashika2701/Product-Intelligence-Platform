-- AI-Powered Business & Product Intelligence Platform Schema
-- Target: MySQL Database Engine (fully compatible with SQLite standard types)

-- Disable foreign key checks for clean drops
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS `experiments`;
DROP TABLE IF EXISTS `orders`;
DROP TABLE IF EXISTS `events`;
DROP TABLE IF EXISTS `sessions`;
DROP TABLE IF EXISTS `users`;

SET FOREIGN_KEY_CHECKS = 1;

-- 1. Users Table
CREATE TABLE `users` (
    `user_id` INT AUTO_INCREMENT PRIMARY KEY,
    `signup_date` DATE NOT NULL,
    `city` VARCHAR(100) NOT NULL,
    `acquisition_channel` VARCHAR(100) NOT NULL,
    `user_segment` VARCHAR(50) NOT NULL,
    INDEX `idx_signup_date` (`signup_date`),
    INDEX `idx_channel` (`acquisition_channel`),
    INDEX `idx_segment` (`user_segment`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. Sessions Table
CREATE TABLE `sessions` (
    `session_id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `session_duration` INT NOT NULL COMMENT 'Duration in seconds',
    `device_type` VARCHAR(50) NOT NULL,
    `session_date` DATE NOT NULL,
    `discount_coupon_applied` TINYINT DEFAULT 0 COMMENT '0 or 1',
    FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE,
    INDEX `idx_user_id` (`user_id`),
    INDEX `idx_session_date` (`session_date`),
    INDEX `idx_device_type` (`device_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. Events Table
CREATE TABLE `events` (
    `event_id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `session_id` INT NOT NULL,
    `event_type` VARCHAR(50) NOT NULL COMMENT 'e.g. App Open, Search, View Product, Add To Cart, Checkout, Purchase',
    `feature_name` VARCHAR(100) DEFAULT NULL,
    `timestamp` DATETIME NOT NULL,
    FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE,
    FOREIGN KEY (`session_id`) REFERENCES `sessions` (`session_id`) ON DELETE CASCADE,
    INDEX `idx_event_user` (`user_id`),
    INDEX `idx_event_session` (`session_id`),
    INDEX `idx_event_type` (`event_type`),
    INDEX `idx_timestamp` (`timestamp`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. Orders Table
CREATE TABLE `orders` (
    `order_id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `session_id` INT NOT NULL,
    `amount` DECIMAL(10, 2) NOT NULL,
    `category` VARCHAR(100) NOT NULL,
    `order_date` DATE NOT NULL,
    FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE,
    FOREIGN KEY (`session_id`) REFERENCES `sessions` (`session_id`) ON DELETE CASCADE,
    INDEX `idx_order_user` (`user_id`),
    INDEX `idx_order_session` (`session_id`),
    INDEX `idx_order_date` (`order_date`),
    INDEX `idx_category` (`category`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. Experiments Table
CREATE TABLE `experiments` (
    `experiment_id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `experiment_group` VARCHAR(100) NOT NULL COMMENT 'e.g. Group A (Old Checkout), Group B (New Checkout)',
    `feature_name` VARCHAR(100) NOT NULL,
    `launch_date` DATE NOT NULL,
    FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE,
    INDEX `idx_exp_user` (`user_id`),
    INDEX `idx_experiment_group` (`experiment_group`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
