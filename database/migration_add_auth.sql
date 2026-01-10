-- Google Stats Database Migration - Add Facebook-Stats Style Authentication
-- Adds 2FA support, session management, CSRF tokens, and security logging
-- Preserves existing users and data

USE `google-stats`;

-- Add missing columns to existing users table (if they don't exist)
ALTER TABLE `users` 
ADD COLUMN IF NOT EXISTS `client_id` INT NOT NULL DEFAULT 1 AFTER `id`,
ADD COLUMN IF NOT EXISTS `failed_login_attempts` INT NOT NULL DEFAULT 0 AFTER `is_active`,
ADD COLUMN IF NOT EXISTS `locked_until` TIMESTAMP NULL AFTER `failed_login_attempts`,
ADD COLUMN IF NOT EXISTS `last_login` TIMESTAMP NULL AFTER `locked_until`,
ADD COLUMN IF NOT EXISTS `two_factor_enabled` BOOLEAN NOT NULL DEFAULT FALSE AFTER `last_login`,
ADD COLUMN IF NOT EXISTS `two_factor_secret` VARCHAR(255) NULL COMMENT 'TOTP secret key' AFTER `two_factor_enabled`,
ADD COLUMN IF NOT EXISTS `two_factor_backup_codes` JSON NULL COMMENT 'Backup recovery codes' AFTER `two_factor_secret`;

-- Add index if it doesn't exist
ALTER TABLE `users` ADD INDEX IF NOT EXISTS `idx_locked_until` (`locked_until`);

-- Create clients table (single-tenant initially, supports multi-tenant expansion)
CREATE TABLE IF NOT EXISTS `clients` (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL DEFAULT 'Default Client',
    domain VARCHAR(255) UNIQUE,
    api_key VARCHAR(64) UNIQUE,
    api_secret VARCHAR(128),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_domain (domain),
    INDEX idx_api_key (api_key),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert default client
INSERT IGNORE INTO `clients` (id, name, domain, is_active) VALUES 
(1, 'Default Client', 'localhost', TRUE);

-- Add foreign key to users table (check if doesn't exist first)
SET @fk_exists = (SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS 
                  WHERE CONSTRAINT_SCHEMA = 'google-stats' 
                  AND TABLE_NAME = 'users' 
                  AND CONSTRAINT_NAME = 'fk_users_client');

SET @sql = IF(@fk_exists = 0, 
    'ALTER TABLE `users` ADD CONSTRAINT `fk_users_client` FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE',
    'SELECT "Foreign key already exists" AS info');

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Sessions table for secure session management
CREATE TABLE IF NOT EXISTS `user_sessions` (
    id VARCHAR(128) PRIMARY KEY,
    user_id INT NOT NULL,
    client_id INT NOT NULL DEFAULT 1,
    ip_address VARCHAR(45) NOT NULL,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_client_id (client_id),
    INDEX idx_expires_at (expires_at),
    INDEX idx_last_activity (last_activity)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- CSRF tokens table for CSRF protection
CREATE TABLE IF NOT EXISTS `csrf_tokens` (
    id INT AUTO_INCREMENT PRIMARY KEY,
    token VARCHAR(64) NOT NULL UNIQUE,
    session_id VARCHAR(128) NOT NULL,
    client_id INT NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
    INDEX idx_session_id (session_id),
    INDEX idx_client_id (client_id),
    INDEX idx_token (token),
    INDEX idx_expires_at (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Login attempts log for security monitoring
CREATE TABLE IF NOT EXISTS `login_attempts` (
    id INT AUTO_INCREMENT PRIMARY KEY,
    client_id INT DEFAULT 1,
    username VARCHAR(50),
    ip_address VARCHAR(45) NOT NULL,
    user_agent TEXT,
    attempt_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    success BOOLEAN NOT NULL DEFAULT FALSE,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
    INDEX idx_client_id (client_id),
    INDEX idx_username (username),
    INDEX idx_ip_address (ip_address),
    INDEX idx_attempt_time (attempt_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Security events log for audit trail
CREATE TABLE IF NOT EXISTS `security_events` (
    id INT AUTO_INCREMENT PRIMARY KEY,
    client_id INT DEFAULT 1,
    event_type VARCHAR(50) NOT NULL,
    user_id INT,
    ip_address VARCHAR(45) NOT NULL,
    user_agent TEXT,
    uri VARCHAR(500),
    details JSON,
    severity ENUM('info', 'warning', 'critical') DEFAULT 'info',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_client_id (client_id),
    INDEX idx_event_type (event_type),
    INDEX idx_user_id (user_id),
    INDEX idx_ip_address (ip_address),
    INDEX idx_severity (severity),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Encrypted credentials table for secure storage of API keys
CREATE TABLE IF NOT EXISTS `credentials` (
    id INT AUTO_INCREMENT PRIMARY KEY,
    client_id INT NOT NULL DEFAULT 1,
    name VARCHAR(100) NOT NULL,
    type ENUM('google_token', 'google_ads', 'api_key', 'database', 'other') NOT NULL,
    description TEXT,
    encrypted_value BLOB NOT NULL COMMENT 'AES-256 encrypted credential value',
    encrypted_key BLOB COMMENT 'AES-256 encrypted key/identifier (optional)',
    created_by INT NOT NULL COMMENT 'User ID who created this credential',
    last_updated_by INT COMMENT 'User ID who last updated this credential',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    expires_at TIMESTAMP NULL COMMENT 'Optional expiration date',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (last_updated_by) REFERENCES users(id) ON DELETE SET NULL,
    UNIQUE KEY unique_client_credential (client_id, name, type),
    INDEX idx_client_id (client_id),
    INDEX idx_type (type),
    INDEX idx_created_by (created_by),
    INDEX idx_is_active (is_active),
    INDEX idx_expires_at (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Reports table for storing generated reports
CREATE TABLE IF NOT EXISTS `reports` (
    id INT AUTO_INCREMENT PRIMARY KEY,
    client_id INT NOT NULL DEFAULT 1,
    user_id INT NOT NULL,
    report_type VARCHAR(100) NOT NULL,
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size_bytes INT,
    date_range_start DATE,
    date_range_end DATE,
    parameters JSON,
    status ENUM('pending', 'processing', 'completed', 'failed') NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_client_id (client_id),
    INDEX idx_user_id (user_id),
    INDEX idx_report_type (report_type),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Update existing users to have client_id if they don't have one
UPDATE `users` SET client_id = 1 WHERE client_id IS NULL OR client_id = 0;

-- Insert default admin user only if no admin users exist (password: admin123)
INSERT INTO `users` (client_id, username, email, password_hash, role, is_active, two_factor_enabled)
SELECT 1, 'admin', 'admin@localhost', '$2y$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 'admin', TRUE, FALSE
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM `users` WHERE role = 'admin');

-- Cleanup procedures
-- Clean up expired sessions (can be scheduled)
DELETE FROM user_sessions WHERE expires_at < NOW();

-- Clean up expired CSRF tokens
DELETE FROM csrf_tokens WHERE expires_at < NOW();

-- Clean up old login attempts (keep last 30 days)
DELETE FROM login_attempts WHERE attempt_time < DATE_SUB(NOW(), INTERVAL 30 DAY);

-- Clean up old security events (keep last 90 days)  
DELETE FROM security_events WHERE created_at < DATE_SUB(NOW(), INTERVAL 90 DAY);
