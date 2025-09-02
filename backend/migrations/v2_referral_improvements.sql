-- V2 友達紹介システム改善のためのマイグレーション
-- LINE連携完了時にボーナス付与、LINE ID重複防止

-- 1. v2_usersテーブルに必要なカラムを追加
ALTER TABLE v2_users 
ADD COLUMN IF NOT EXISTS referral_bonus_granted BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS line_connected_referral_count INTEGER DEFAULT 0;

-- 2. v2_referral_historyテーブルのステータスを拡張
ALTER TABLE v2_referral_history 
ADD COLUMN IF NOT EXISTS line_connected_at TIMESTAMP,
ALTER COLUMN status SET DEFAULT 'pending';

-- statusの値を更新（既存のcompletedをpendingに変更）
UPDATE v2_referral_history 
SET status = 'pending' 
WHERE status = 'completed' AND line_connected_at IS NULL;

-- 3. LINE ID重複検出用のテーブル
CREATE TABLE IF NOT EXISTS v2_line_duplicate_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    line_user_id VARCHAR(255) NOT NULL,
    attempted_by_user_id UUID REFERENCES v2_users(id),
    existing_user_ids UUID[] NOT NULL,
    attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- インデックス作成
CREATE INDEX IF NOT EXISTS idx_line_duplicate_attempts_line_user_id 
ON v2_line_duplicate_attempts(line_user_id);

CREATE INDEX IF NOT EXISTS idx_line_duplicate_attempts_user_id 
ON v2_line_duplicate_attempts(attempted_by_user_id);

-- 4. LINE連携履歴テーブル（監査用）
CREATE TABLE IF NOT EXISTS v2_line_connection_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES v2_users(id),
    line_user_id VARCHAR(255),
    connected_at TIMESTAMP,
    status VARCHAR(50) NOT NULL, -- 'success', 'disconnected', 'blocked'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- インデックス作成
CREATE INDEX IF NOT EXISTS idx_line_connection_history_user_id 
ON v2_line_connection_history(user_id);

CREATE INDEX IF NOT EXISTS idx_line_connection_history_line_user_id 
ON v2_line_connection_history(line_user_id);

-- 5. v2_usersテーブルのline_user_idにユニーク制約を追加（重複防止）
ALTER TABLE v2_users 
ADD CONSTRAINT unique_line_user_id UNIQUE (line_user_id);

-- 6. 紹介履歴のステータス用のENUM型を作成（PostgreSQL）
DO $$ BEGIN
    CREATE TYPE referral_status AS ENUM ('pending', 'line_connected', 'expired', 'cancelled');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- 既存のカラムをENUM型に変更（可能な場合）
-- ALTER TABLE v2_referral_history 
-- ALTER COLUMN status TYPE referral_status USING status::referral_status;

-- 7. 統計ビューの作成（オプション）
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

-- 8. 不正利用検出用のビュー
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

-- 9. インデックスの追加（パフォーマンス改善）
CREATE INDEX IF NOT EXISTS idx_v2_users_referred_by 
ON v2_users(referred_by);

CREATE INDEX IF NOT EXISTS idx_v2_users_referral_code 
ON v2_users(referral_code);

CREATE INDEX IF NOT EXISTS idx_v2_referral_history_referrer_status 
ON v2_referral_history(referrer_id, status);

-- 10. 既存データの移行（必要に応じて）
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

-- コメント追加
COMMENT ON TABLE v2_line_duplicate_attempts IS 'LINE ID重複利用の検出記録';
COMMENT ON TABLE v2_line_connection_history IS 'LINE連携の履歴（監査用）';
COMMENT ON COLUMN v2_users.referral_bonus_granted IS '紹介ボーナス付与済みフラグ';
COMMENT ON COLUMN v2_users.line_connected_referral_count IS 'LINE連携済みの紹介人数';
COMMENT ON COLUMN v2_referral_history.line_connected_at IS 'LINE連携完了日時';