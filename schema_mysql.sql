-- POS + QR Multi-Tenant Schema for MySQL 8.0

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for tenants
-- ----------------------------
CREATE TABLE IF NOT EXISTS tenants (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    brand_name VARCHAR(255) DEFAULT 'Restaurant POS',
    currency_symbol VARCHAR(16) DEFAULT '$',
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for tenant_feedback
-- ----------------------------
CREATE TABLE IF NOT EXISTS tenant_feedback (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL,
    table_number VARCHAR(64) DEFAULT NULL,
    session_id VARCHAR(64) DEFAULT NULL,
    customer_name VARCHAR(255) DEFAULT NULL,
    rating INT NOT NULL DEFAULT 5,
    food_rating INT DEFAULT 5,
    service_rating INT DEFAULT 5,
    comments TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_feedback_tenant (tenant_id),
    INDEX idx_feedback_created (tenant_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for users
-- ----------------------------
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL,
    username VARCHAR(128) NOT NULL,
    full_name VARCHAR(255) DEFAULT NULL,
    password_hash VARCHAR(255) NOT NULL,
    demo_password_plain VARCHAR(255) DEFAULT NULL,
    role VARCHAR(32) NOT NULL DEFAULT 'cashier',
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_tenant_username (tenant_id, username),
    INDEX idx_users_tenant (tenant_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for sessions
-- ----------------------------
CREATE TABLE IF NOT EXISTS sessions (
    id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL,
    pax INT DEFAULT 1,
    table_number VARCHAR(64) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    guest_name VARCHAR(255) DEFAULT NULL,
    dp_amount INT DEFAULT 0,
    dp_method VARCHAR(64) DEFAULT NULL,
    dp_paid_at DATETIME DEFAULT NULL,
    note TEXT DEFAULT NULL,
    status VARCHAR(32) DEFAULT 'active',
    closed_at DATETIME DEFAULT NULL,
    opened_by_user_id INT DEFAULT NULL,
    closed_by_user_id INT DEFAULT NULL,
    split_labels TEXT DEFAULT NULL,
    split_meta JSON DEFAULT NULL,
    lock_user_id INT DEFAULT NULL,
    lock_until DATETIME DEFAULT NULL,
    lock_nonce VARCHAR(64) DEFAULT NULL,
    lock_acquired_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    billing_started_at DATETIME DEFAULT NULL,
    service_type VARCHAR(32) NOT NULL DEFAULT 'dine_in',
    pickup_time DATETIME DEFAULT NULL,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    reopened_at DATETIME DEFAULT NULL,
    reopened_by_user_id INT DEFAULT NULL,
    INDEX idx_sessions_tenant (tenant_id),
    INDEX idx_sessions_table (tenant_id, table_number, status),
    INDEX idx_sessions_status (tenant_id, status),
    INDEX idx_sessions_created (tenant_id, created_at),
    INDEX idx_sessions_closed (tenant_id, closed_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for order_items
-- ----------------------------
CREATE TABLE IF NOT EXISTS order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL,
    session_id VARCHAR(64) NOT NULL,
    table_number VARCHAR(64) NOT NULL,
    item_name VARCHAR(255) NOT NULL,
    qty DECIMAL(10,1) NOT NULL,
    price INT NOT NULL,
    total_price INT NOT NULL,
    sauce VARCHAR(255) DEFAULT NULL,
    note TEXT DEFAULT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'new',
    `timestamp` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by_user_id INT DEFAULT NULL,
    updated_by_user_id INT DEFAULT NULL,
    bill_group VARCHAR(64) DEFAULT NULL,
    void_qty DECIMAL(10,1) NOT NULL DEFAULT 0.0,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_order_items_tenant (tenant_id),
    INDEX idx_order_items_session (tenant_id, session_id, bill_group),
    INDEX idx_order_items_status (tenant_id, status),
    INDEX idx_order_items_ts (tenant_id, `timestamp`),
    CONSTRAINT fk_order_items_session FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for payments
-- ----------------------------
CREATE TABLE IF NOT EXISTS payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL,
    session_id VARCHAR(64) DEFAULT NULL,
    amount INT NOT NULL DEFAULT 0,
    method VARCHAR(64) DEFAULT NULL,
    paid_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    cash_received INT DEFAULT NULL,
    change_given INT DEFAULT NULL,
    discount_percent INT DEFAULT 0,
    discount_amount INT DEFAULT 0,
    tax INT DEFAULT 0,
    service INT DEFAULT 0,
    total_before_discount INT DEFAULT 0,
    card_type VARCHAR(64) DEFAULT NULL,
    created_by_user_id INT DEFAULT NULL,
    bill_group VARCHAR(64) DEFAULT NULL,
    dp_applied_amount INT DEFAULT 0,
    is_refund TINYINT(1) NOT NULL DEFAULT 0,
    refund_of INT DEFAULT NULL,
    refund_reason TEXT DEFAULT NULL,
    refunded_by_user_id INT DEFAULT NULL,
    is_dp TINYINT(1) NOT NULL DEFAULT 0,
    INDEX idx_payments_tenant (tenant_id),
    INDEX idx_payments_session (tenant_id, session_id),
    INDEX idx_payments_paid_at (tenant_id, paid_at),
    INDEX idx_payments_is_refund (tenant_id, is_refund)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for reservations
-- ----------------------------
CREATE TABLE IF NOT EXISTS reservations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL,
    guest_name VARCHAR(255) NOT NULL,
    phone VARCHAR(64) DEFAULT NULL,
    pax INT NOT NULL DEFAULT 1,
    date DATE NOT NULL,
    `time` TIME NOT NULL,
    notes TEXT DEFAULT NULL,
    status VARCHAR(32) DEFAULT 'pending',
    table_number VARCHAR(64) DEFAULT NULL,
    session_id VARCHAR(64) DEFAULT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by_user_id INT DEFAULT NULL,
    confirmed_by_user_id INT DEFAULT NULL,
    seated_by_user_id INT DEFAULT NULL,
    dp_amount INT NOT NULL DEFAULT 0,
    dp_method VARCHAR(64) DEFAULT NULL,
    dp_paid_at DATETIME DEFAULT NULL,
    INDEX idx_res_tenant (tenant_id),
    INDEX idx_res_date_time (tenant_id, date, `time`),
    INDEX idx_res_status (tenant_id, status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for reservation_items
-- ----------------------------
CREATE TABLE IF NOT EXISTS reservation_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL,
    reservation_id INT NOT NULL,
    item_name VARCHAR(255) NOT NULL,
    qty INT NOT NULL DEFAULT 1,
    price INT NOT NULL DEFAULT 0,
    sauce VARCHAR(255) DEFAULT NULL,
    note TEXT DEFAULT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by_user_id INT DEFAULT NULL,
    INDEX idx_res_items_tenant (tenant_id),
    INDEX idx_res_items_res (tenant_id, reservation_id),
    CONSTRAINT fk_res_items_res FOREIGN KEY (reservation_id) REFERENCES reservations(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for floor_layouts
-- ----------------------------
CREATE TABLE IF NOT EXISTS floor_layouts (
    tenant_id VARCHAR(64) NOT NULL,
    floor VARCHAR(64) NOT NULL,
    grid_cols INT NOT NULL DEFAULT 12,
    grid_row_px INT NOT NULL DEFAULT 90,
    grid_gap_px INT NOT NULL DEFAULT 6,
    boxes JSON NOT NULL,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    updated_by_user_id INT DEFAULT NULL,
    PRIMARY KEY (tenant_id, floor)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for qr_orders
-- ----------------------------
CREATE TABLE IF NOT EXISTS qr_orders (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL,
    table_number VARCHAR(64) NOT NULL,
    session_id VARCHAR(64) DEFAULT NULL,
    guest_name VARCHAR(255) DEFAULT NULL,
    items JSON NOT NULL,
    notes TEXT DEFAULT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'new',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    sent_at DATETIME DEFAULT NULL,
    INDEX idx_qr_tenant (tenant_id),
    INDEX idx_qr_table (tenant_id, table_number, status),
    INDEX idx_qr_status (tenant_id, status, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Default Tenants Seed
-- ----------------------------
INSERT INTO tenants (id, name, brand_name, currency_symbol, is_active) VALUES
('default', 'Main Branch Restaurant', 'OpenPOS & QR Gourmet', '$', 1),
('branch2', 'Downtown Bistro', 'Downtown Gourmet & Bistro', '$', 1)
ON DUPLICATE KEY UPDATE name=VALUES(name);

-- ----------------------------
-- Default Users Seed
-- ----------------------------
-- Passwords:
-- admin / admin123  (bcrypt hash)
-- cashier / cashier123
-- waiter / waiter123
-- default tenant admin:
INSERT INTO users (id, tenant_id, username, full_name, password_hash, demo_password_plain, role, is_active) VALUES
(1, 'default', 'admin', 'System Administrator', '$2b$12$6yO.K8bSgBfVv9V5dC5w8eb93G2bL6dD6HjT3.407OekmI78c6Vl2', 'admin123', 'admin', 1),
(2, 'default', 'cashier', 'Main Cashier', '$2b$12$6yO.K8bSgBfVv9V5dC5w8eb93G2bL6dD6HjT3.407OekmI78c6Vl2', 'cashier123', 'cashier', 1),
(3, 'default', 'waiter', 'Front Waiter', '$2b$12$6yO.K8bSgBfVv9V5dC5w8eb93G2bL6dD6HjT3.407OekmI78c6Vl2', 'waiter123', 'waiter', 1),
(4, 'branch2', 'admin', 'Downtown Admin', '$2b$12$6yO.K8bSgBfVv9V5dC5w8eb93G2bL6dD6HjT3.407OekmI78c6Vl2', 'admin123', 'admin', 1)
ON DUPLICATE KEY UPDATE full_name=VALUES(full_name);

SET FOREIGN_KEY_CHECKS = 1;
