-- =====================================================
-- V2システム差分マイグレーション
-- 実行日: 2025-01-31
-- 説明: 既存のV2テーブルに不足しているカラムと新規テーブルのみ追加
-- =====================================================

-- =====================================================
-- 1. v2_usersテーブルへのカラム追加（不足分のみ）
-- =====================================================

-- 友達紹介関連の新規カラム
ALTER TABLE v2_users 
ADD COLUMN IF NOT EXISTS referral_bonus_granted BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS line_connected_referral_count INTEGER DEFAULT 0;

-- =====================================================
-- 2. v2_referral_historyテーブルへのカラム追加
-- =====================================================

-- LINE連携完了時のタイムスタンプ追加
ALTER TABLE v2_referral_history 
ADD COLUMN IF NOT EXISTS line_connected_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'pending';

-- statusカラムが既に存在する場合は、デフォルト値を更新
DO $$ 
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'v2_referral_history' 
        AND column_name = 'status'
    ) THEN
        ALTER TABLE v2_referral_history 
        ALTER COLUMN status SET DEFAULT 'pending';
    END IF;
END $$;

-- =====================================================
-- 3. 新規テーブル作成（存在しない場合のみ）
-- =====================================================

-- LINE ID重複検出用のテーブル
CREATE TABLE IF NOT EXISTS v2_line_duplicate_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    line_user_id VARCHAR(255) NOT NULL,
    attempted_by_user_id UUID REFERENCES v2_users(id),
    existing_user_ids UUID[] NOT NULL,
    attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- LINE連携履歴テーブル（監査用）
CREATE TABLE IF NOT EXISTS v2_line_connection_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES v2_users(id),
    line_user_id VARCHAR(255),
    connected_at TIMESTAMP,
    status VARCHAR(50) NOT NULL, -- success, disconnected, blocked
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- LINE OAuth セッション管理テーブル
CREATE TABLE IF NOT EXISTS v2_line_oauth_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    state VARCHAR(255) UNIQUE NOT NULL,
    user_id UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL
);

-- =====================================================
-- 4. インデックス作成（存在しない場合のみ）
-- =====================================================

-- v2_line_duplicate_attempts用インデックス
CREATE INDEX IF NOT EXISTS idx_v2_line_duplicate_attempts_line_user_id 
ON v2_line_duplicate_attempts(line_user_id);

CREATE INDEX IF NOT EXISTS idx_v2_line_duplicate_attempts_user_id 
ON v2_line_duplicate_attempts(attempted_by_user_id);

-- v2_line_connection_history用インデックス
CREATE INDEX IF NOT EXISTS idx_v2_line_connection_history_user_id 
ON v2_line_connection_history(user_id);

CREATE INDEX IF NOT EXISTS idx_v2_line_connection_history_line_user_id 
ON v2_line_connection_history(line_user_id);

-- v2_line_oauth_sessions用インデックス
CREATE INDEX IF NOT EXISTS idx_v2_line_oauth_sessions_state 
ON v2_line_oauth_sessions(state);

CREATE INDEX IF NOT EXISTS idx_v2_line_oauth_sessions_expires_at 
ON v2_line_oauth_sessions(expires_at);

-- v2_referral_history用インデックス
CREATE INDEX IF NOT EXISTS idx_v2_referral_history_referrer_status 
ON v2_referral_history(referrer_id, status);

-- =====================================================
-- 5. ビューの作成または更新
-- =====================================================

-- 紹介統計ビュー
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

-- 不正利用検出ビュー
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
-- 6. 既存データの更新
-- =====================================================

-- 既存のstatusカラムがNULLの場合、デフォルト値を設定
UPDATE v2_referral_history 
SET status = 'pending' 
WHERE status IS NULL;

-- 既存のLINE連携済みユーザーで紹介関係があるものを更新
UPDATE v2_referral_history rh
SET 
    status = 'line_connected',
    line_connected_at = u.line_connected_at
FROM v2_users u
WHERE 
    rh.referred_id = u.id 
    AND u.line_user_id IS NOT NULL 
    AND (rh.status = 'pending' OR rh.status IS NULL);

-- 紹介者のLINE連携済み紹介人数を再計算
UPDATE v2_users u
SET line_connected_referral_count = COALESCE((
    SELECT COUNT(*)
    FROM v2_referral_history rh
    WHERE rh.referrer_id = u.id AND rh.status = 'line_connected'
), 0)
WHERE EXISTS (
    SELECT 1 FROM v2_referral_history WHERE referrer_id = u.id
);

-- =====================================================
-- 7. テーブルコメント追加
-- =====================================================

COMMENT ON TABLE v2_line_duplicate_attempts IS 'LINE ID重複利用の検出記録';
COMMENT ON TABLE v2_line_connection_history IS 'LINE連携の履歴（監査用）';
COMMENT ON TABLE v2_line_oauth_sessions IS 'LINE OAuthセッション管理';

COMMENT ON COLUMN v2_users.referral_bonus_granted IS '紹介ボーナス付与済みフラグ';
COMMENT ON COLUMN v2_users.line_connected_referral_count IS 'LINE連携済みの紹介人数';
COMMENT ON COLUMN v2_referral_history.line_connected_at IS 'LINE連携完了日時';
COMMENT ON COLUMN v2_referral_history.status IS '紹介ステータス（pending/line_connected/expired/cancelled）';

-- =====================================================
-- 8. 確認クエリ
-- =====================================================

-- 実行後の確認用
DO $$
DECLARE
    missing_tables TEXT := '';
    missing_columns TEXT := '';
BEGIN
    -- 必要なテーブルの存在確認
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'v2_line_duplicate_attempts') THEN
        missing_tables := missing_tables || 'v2_line_duplicate_attempts, ';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'v2_line_connection_history') THEN
        missing_tables := missing_tables || 'v2_line_connection_history, ';
    END IF;
    
    -- 必要なカラムの存在確認
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'v2_users' AND column_name = 'referral_bonus_granted') THEN
        missing_columns := missing_columns || 'v2_users.referral_bonus_granted, ';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'v2_users' AND column_name = 'line_connected_referral_count') THEN
        missing_columns := missing_columns || 'v2_users.line_connected_referral_count, ';
    END IF;
    
    -- 結果表示
    IF missing_tables = '' AND missing_columns = '' THEN
        RAISE NOTICE 'V2差分マイグレーション完了: すべての必要な要素が存在します';
    ELSE
        IF missing_tables != '' THEN
            RAISE WARNING '不足しているテーブル: %', missing_tables;
        END IF;
        IF missing_columns != '' THEN
            RAISE WARNING '不足しているカラム: %', missing_columns;
        END IF;
    END IF;
END $$;