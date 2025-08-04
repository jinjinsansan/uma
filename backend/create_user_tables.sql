-- D-Logic AI ユーザー管理システム用テーブル作成
-- 実行前にmykeidadbデータベースに接続してください

-- 1. usersテーブル
CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    google_id VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    image_url TEXT,
    subscription_type ENUM('free', 'premium') DEFAULT 'free',
    free_trial_start_date DATETIME,
    free_trial_end_date DATETIME,
    premium_start_date DATETIME,
    premium_end_date DATETIME,
    total_queries_used INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_google_id (google_id),
    INDEX idx_email (email),
    INDEX idx_subscription_type (subscription_type)
);

-- 2. user_queriesテーブル（使用履歴）
CREATE TABLE IF NOT EXISTS user_queries (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    query_type ENUM('horse_analysis', 'race_analysis', 'general_chat') NOT NULL,
    query_text TEXT,
    response_text LONGTEXT,
    processing_time_ms INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_query_type (query_type),
    INDEX idx_created_at (created_at)
);

-- 3. user_paymentsテーブル（決済履歴）
CREATE TABLE IF NOT EXISTS user_payments (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    payment_provider ENUM('stripe', 'paypal') NOT NULL,
    payment_intent_id VARCHAR(255),
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'JPY',
    subscription_period INT, -- 月数
    status ENUM('pending', 'completed', 'failed', 'refunded') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
);

-- 4. line_usersテーブル（LINE連携）
CREATE TABLE IF NOT EXISTS line_users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    line_user_id VARCHAR(255) UNIQUE NOT NULL,
    tickets_received INT DEFAULT 0,
    friend_added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_line_user_id (line_user_id)
);

-- テーブル作成完了メッセージ
SELECT 'User management tables created successfully!' as message;