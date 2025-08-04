-- LINE連携用テーブル追加
-- 既存のcreate_user_tables.sqlに追加実行

-- 5. line_verification_codesテーブル（認証コード管理）
CREATE TABLE IF NOT EXISTS line_verification_codes (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    code VARCHAR(10) NOT NULL,
    used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_code (code),
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at)
);

-- 6. line_pending_friendsテーブル（友達追加済みだが未連携のユーザー）
CREATE TABLE IF NOT EXISTS line_pending_friends (
    id INT PRIMARY KEY AUTO_INCREMENT,
    line_user_id VARCHAR(255) UNIQUE NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_line_user_id (line_user_id),
    INDEX idx_added_at (added_at)
);

-- 7. line_messagesテーブル（メッセージ履歴）
CREATE TABLE IF NOT EXISTS line_messages (
    id INT PRIMARY KEY AUTO_INCREMENT,
    line_user_id VARCHAR(255) NOT NULL,
    user_id INT,
    message_type ENUM('received', 'sent') NOT NULL,
    message_text TEXT,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_line_user_id (line_user_id),
    INDEX idx_user_id (user_id),
    INDEX idx_sent_at (sent_at)
);

-- 既存のline_usersテーブルにカラム追加
ALTER TABLE line_users 
ADD COLUMN unfriend_at TIMESTAMP NULL,
ADD INDEX idx_unfriend_at (unfriend_at);

-- LINE連携テーブル作成完了メッセージ
SELECT 'LINE integration tables created successfully!' as message;