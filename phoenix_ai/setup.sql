-- ============================================================
-- Phoenix AI – Customer Support System
-- Database Setup Script
-- ============================================================

CREATE DATABASE IF NOT EXISTS phoenix_ai;
USE phoenix_ai;

-- ─────────────────────────────────────────────
-- Table: users
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(100)        NOT NULL,
    email       VARCHAR(150) UNIQUE NOT NULL,
    password    VARCHAR(255)        NOT NULL,
    role        ENUM('user','admin') DEFAULT 'user',
    created_at  DATETIME            DEFAULT CURRENT_TIMESTAMP
);

-- ─────────────────────────────────────────────
-- Table: complaints
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS complaints (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    ticket_id   VARCHAR(20)  UNIQUE NOT NULL,
    category    VARCHAR(100)        NOT NULL,
    description TEXT                NOT NULL,
    status      ENUM('Open','Closed') DEFAULT 'Open',
    created_at  DATETIME            DEFAULT CURRENT_TIMESTAMP
);

-- ─────────────────────────────────────────────
-- Table: orders
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS orders (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    order_id    VARCHAR(50)  UNIQUE NOT NULL,
    status      VARCHAR(50),
    created_at  DATETIME            DEFAULT CURRENT_TIMESTAMP
);

-- ─────────────────────────────────────────────
-- Sample Data
-- ─────────────────────────────────────────────

-- Sample users (passwords are plain-text for demo; use hashing in production)
INSERT IGNORE INTO users (name, email, password, role) VALUES
('Admin User',  'admin@phoenix.ai',  'admin123',  'admin'),
('Alice Kumar', 'alice@example.com', 'pass1234',  'user'),
('Bob Sharma',  'bob@example.com',   'pass5678',  'user');

-- Sample complaints
INSERT IGNORE INTO complaints (ticket_id, category, description, status) VALUES
('ST101', 'Delivery',  'My order has not arrived after 10 days.',          'Open'),
('ST102', 'Payment',   'Double charged for order N642DT684.',               'Open'),
('ST103', 'Refund',    'Refund not credited after 15 business days.',       'Closed'),
('ST104', 'Technical', 'Unable to login to my account since yesterday.',    'Open'),
('ST105', 'Delivery',  'Package delivered to wrong address.',               'Closed');

-- Sample orders
INSERT IGNORE INTO orders (order_id, status) VALUES
('N642DT684', 'shipped'),
('N123AB456', 'delivered'),
('N789CD012', 'processing'),
('N321EF654', 'out for delivery'),
('N555GH999', 'delivered');
