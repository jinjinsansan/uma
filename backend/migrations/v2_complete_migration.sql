-- =====================================================
-- V2システム完全マイグレーション
-- 実行日: 2025-01-31
-- 説明: V2ポイント制システム、友達紹介改善、LINE連携の完全実装
-- =====================================================

-- =====================================================
-- 1. V2ユーザーテーブル
-- =====================================================
CREATE TABLE IF NOT EXISTS v2_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    google_id VARCHAR(255) UNIQUE,
    avatar_url TEXT,
    
    -- LINE連携
    line_user_id VARCHAR(255) UNIQUE,
    line_display_name VARCHAR(255),
    line_picture_url TEXT,
    line_connected_at TIMESTAMP,
    line_access_token TEXT,
    
    -- 友達紹介
    referral_code VARCHAR(6) UNIQUE,
    referral_count INTEGER DEFAULT 0,
    referred_by UUID REFERENCES v2_users(id),
    referred_at TIMESTAMP,
    referral_bonus_granted BOOLEAN DEFAULT FALSE,
    line_connected_referral_count INTEGER DEFAULT 0,
    
    -- システム情報
    last_login_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- インデックス作成
CREATE INDEX IF NOT EXISTS idx_v2_users_email ON v2_users(email);
CREATE INDEX IF NOT EXISTS idx_v2_users_google_id ON v2_users(google_id);
CREATE INDEX IF NOT EXISTS idx_v2_users_line_user_id ON v2_users(line_user_id);
CREATE INDEX IF NOT EXISTS idx_v2_users_referral_code ON v2_users(referral_code);
CREATE INDEX IF NOT EXISTS idx_v2_users_referred_by ON v2_users(referred_by);

-- =====================================================
-- 2. V2ポイント管理テーブル
-- =====================================================
CREATE TABLE IF NOT EXISTS v2_user_points (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES v2_users(id) ON DELETE CASCADE,
    current_points INTEGER DEFAULT 0,
    total_earned INTEGER DEFAULT 0,
    total_spent INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id)
);

CREATE INDEX IF NOT EXISTS idx_v2_user_points_user_id ON v2_user_points(user_id);

-- =====================================================
-- 3. V2ポイント取引履歴テーブル
-- =====================================================
CREATE TABLE IF NOT EXISTS v2_point_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES v2_users(id) ON DELETE CASCADE,
    amount INTEGER NOT NULL,
    balance_after INTEGER NOT NULL,
    transaction_type VARCHAR(50) NOT NULL,
    description TEXT,
    related_entity_type VARCHAR(50),
    related_entity_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_v2_point_transactions_user_id ON v2_point_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_v2_point_transactions_type ON v2_point_transactions(transaction_type);
CREATE INDEX IF NOT EXISTS idx_v2_point_transactions_created_at ON v2_point_transactions(created_at);

-- =====================================================
-- 4. V2友達紹介履歴テーブル
-- =====================================================
CREATE TABLE IF NOT EXISTS v2_referral_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    referrer_id UUID REFERENCES v2_users(id),
    referred_id UUID REFERENCES v2_users(id),
    referral_code VARCHAR(6),
    status VARCHAR(50) DEFAULT 'pending', -- pending, line_connected, expired, cancelled
    line_connected_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_v2_referral_history_referrer_id ON v2_referral_history(referrer_id);
CREATE INDEX IF NOT EXISTS idx_v2_referral_history_referred_id ON v2_referral_history(referred_id);
CREATE INDEX IF NOT EXISTS idx_v2_referral_history_status ON v2_referral_history(status);
CREATE INDEX IF NOT EXISTS idx_v2_referral_history_referrer_status ON v2_referral_history(referrer_id, status);

-- =====================================================
-- 5. LINE ID重複検出テーブル
-- =====================================================
CREATE TABLE IF NOT EXISTS v2_line_duplicate_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    line_user_id VARCHAR(255) NOT NULL,
    attempted_by_user_id UUID REFERENCES v2_users(id),
    existing_user_ids UUID[] NOT NULL,
    attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_v2_line_duplicate_attempts_line_user_id 
ON v2_line_duplicate_attempts(line_user_id);

CREATE INDEX IF NOT EXISTS idx_v2_line_duplicate_attempts_user_id 
ON v2_line_duplicate_attempts(attempted_by_user_id);

-- =====================================================
-- 6. LINE連携履歴テーブル（監査用）
-- =====================================================
CREATE TABLE IF NOT EXISTS v2_line_connection_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES v2_users(id),
    line_user_id VARCHAR(255),
    connected_at TIMESTAMP,
    status VARCHAR(50) NOT NULL, -- success, disconnected, blocked
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_v2_line_connection_history_user_id 
ON v2_line_connection_history(user_id);

CREATE INDEX IF NOT EXISTS idx_v2_line_connection_history_line_user_id 
ON v2_line_connection_history(line_user_id);

-- =====================================================
-- 7. LINE OAuth セッション管理テーブル
-- =====================================================
CREATE TABLE IF NOT EXISTS v2_line_oauth_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    state VARCHAR(255) UNIQUE NOT NULL,
    user_id UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_v2_line_oauth_sessions_state ON v2_line_oauth_sessions(state);
CREATE INDEX IF NOT EXISTS idx_v2_line_oauth_sessions_expires_at ON v2_line_oauth_sessions(expires_at);

-- =====================================================
-- 8. V2チャットセッションテーブル
-- =====================================================
CREATE TABLE IF NOT EXISTS v2_chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES v2_users(id) ON DELETE CASCADE,
    race_id VARCHAR(255) NOT NULL,
    race_date DATE NOT NULL,
    venue VARCHAR(50) NOT NULL,
    race_number INTEGER NOT NULL,
    race_name VARCHAR(255),
    points_consumed INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_v2_chat_sessions_user_id ON v2_chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_v2_chat_sessions_race_id ON v2_chat_sessions(race_id);
CREATE INDEX IF NOT EXISTS idx_v2_chat_sessions_created_at ON v2_chat_sessions(created_at);

-- =====================================================
-- 9. V2チャットメッセージテーブル
-- =====================================================
CREATE TABLE IF NOT EXISTS v2_chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES v2_chat_sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL, -- user, assistant, system
    content TEXT NOT NULL,
    ai_type VARCHAR(20), -- imlogic, dlogic, ilogic, viewlogic
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_v2_chat_messages_session_id ON v2_chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_v2_chat_messages_created_at ON v2_chat_messages(created_at);

-- =====================================================
-- 10. V2レーススコアテーブル
-- =====================================================
CREATE TABLE IF NOT EXISTS v2_race_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    race_id VARCHAR(255) NOT NULL,
    race_date DATE NOT NULL,
    venue VARCHAR(50) NOT NULL,
    race_number INTEGER NOT NULL,
    race_name VARCHAR(255),
    
    -- 馬情報
    horses TEXT[],
    jockeys TEXT[],
    posts INTEGER[],
    horse_numbers INTEGER[],
    sex_ages TEXT[],
    weights DECIMAL[],
    trainers TEXT[],
    odds DECIMAL[],
    popularities INTEGER[],
    
    -- レース条件
    distance VARCHAR(50),
    track_condition VARCHAR(20),
    grade VARCHAR(50),
    
    -- 分析結果
    dlogic_scores JSONB,
    ilogic_scores JSONB,
    viewlogic_scores JSONB,
    imlogic_scores JSONB,
    
    -- 結果
    result JSONB,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(race_id)
);

CREATE INDEX IF NOT EXISTS idx_v2_race_scores_race_id ON v2_race_scores(race_id);
CREATE INDEX IF NOT EXISTS idx_v2_race_scores_race_date ON v2_race_scores(race_date);
CREATE INDEX IF NOT EXISTS idx_v2_race_scores_venue ON v2_race_scores(venue);

-- =====================================================
-- 11. 統計ビューの作成
-- =====================================================
CREATE OR REPLACE VIEW v2_referral_statistics AS
SELECT 
    u.id as user_id,
    u.email,
    u.referral_code,
    COUNT(DISTINCT rh_pending.referred_id) as pending_referrals,
    COUNT(DISTINCT rh_connected.referred_id) as line_connected_referrals,
    u.line_connected_referral_count,
    CASE 
        WHEN u.line_connected_referral_count = 0 THEN 0
        WHEN u.line_connected_referral_count = 1 THEN 30
        WHEN u.line_connected_referral_count = 2 THEN 40
        WHEN u.line_connected_referral_count = 3 THEN 50
        WHEN u.line_connected_referral_count = 4 THEN 60
        ELSE 100
    END as next_bonus_points
FROM v2_users u
LEFT JOIN v2_referral_history rh_pending 
    ON u.id = rh_pending.referrer_id AND rh_pending.status = 'pending'
LEFT JOIN v2_referral_history rh_connected 
    ON u.id = rh_connected.referrer_id AND rh_connected.status = 'line_connected'
GROUP BY u.id, u.email, u.referral_code, u.line_connected_referral_count;

-- =====================================================
-- 12. 不正利用検出ビュー
-- =====================================================
CREATE OR REPLACE VIEW v2_suspicious_line_usage AS
SELECT 
    line_user_id,
    COUNT(DISTINCT attempted_by_user_id) as attempt_count,
    ARRAY_AGG(DISTINCT attempted_by_user_id) as attempted_by_users,
    MAX(attempted_at) as last_attempt,
    MIN(attempted_at) as first_attempt
FROM v2_line_duplicate_attempts
GROUP BY line_user_id
HAVING COUNT(DISTINCT attempted_by_user_id) > 1
ORDER BY attempt_count DESC;

-- =====================================================
-- 13. 自動更新トリガー
-- =====================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- v2_usersテーブル用
CREATE TRIGGER update_v2_users_updated_at 
    BEFORE UPDATE ON v2_users 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- v2_user_pointsテーブル用
CREATE TRIGGER update_v2_user_points_updated_at 
    BEFORE UPDATE ON v2_user_points 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- v2_race_scoresテーブル用
CREATE TRIGGER update_v2_race_scores_updated_at 
    BEFORE UPDATE ON v2_race_scores 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- 14. 既存データの移行（必要に応じて）
-- =====================================================
-- 既存のLINE連携済みユーザーで紹介関係があるものを更新
UPDATE v2_referral_history rh
SET 
    status = 'line_connected',
    line_connected_at = u.line_connected_at
FROM v2_users u
WHERE 
    rh.referred_id = u.id 
    AND u.line_user_id IS NOT NULL 
    AND rh.status = 'pending';

-- 紹介者のLINE連携済み紹介人数を再計算
UPDATE v2_users u
SET line_connected_referral_count = (
    SELECT COUNT(*)
    FROM v2_referral_history rh
    WHERE rh.referrer_id = u.id AND rh.status = 'line_connected'
)
WHERE EXISTS (
    SELECT 1 FROM v2_referral_history WHERE referrer_id = u.id
);

-- =====================================================
-- 15. テーブルコメント追加
-- =====================================================
COMMENT ON TABLE v2_users IS 'V2システムユーザー管理';
COMMENT ON TABLE v2_user_points IS 'V2ユーザーポイント残高';
COMMENT ON TABLE v2_point_transactions IS 'V2ポイント取引履歴';
COMMENT ON TABLE v2_referral_history IS 'V2友達紹介履歴';
COMMENT ON TABLE v2_line_duplicate_attempts IS 'LINE ID重複利用の検出記録';
COMMENT ON TABLE v2_line_connection_history IS 'LINE連携の履歴（監査用）';
COMMENT ON TABLE v2_line_oauth_sessions IS 'LINE OAuthセッション管理';
COMMENT ON TABLE v2_chat_sessions IS 'V2チャットセッション';
COMMENT ON TABLE v2_chat_messages IS 'V2チャットメッセージ';
COMMENT ON TABLE v2_race_scores IS 'V2レース分析スコア';

COMMENT ON COLUMN v2_users.referral_bonus_granted IS '紹介ボーナス付与済みフラグ';
COMMENT ON COLUMN v2_users.line_connected_referral_count IS 'LINE連携済みの紹介人数';
COMMENT ON COLUMN v2_referral_history.line_connected_at IS 'LINE連携完了日時';

-- =====================================================
-- 完了メッセージ
-- =====================================================
DO $$
BEGIN
    RAISE NOTICE 'V2システムマイグレーションが完了しました';
    RAISE NOTICE 'テーブル作成: 10個';
    RAISE NOTICE 'ビュー作成: 2個';
    RAISE NOTICE 'トリガー作成: 3個';
    RAISE NOTICE 'インデックス作成: 完了';
END $$;