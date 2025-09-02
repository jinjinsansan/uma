-- V2 IMLogic設定永続化システム
-- ユーザーごとに最新の設定を保持し、すべてのチャットセッションで使用

-- 1. is_activeカラムを追加（既存テーブルに）
ALTER TABLE v2_imlogic_settings 
ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT true;

-- 2. インデックスを追加（検索高速化）
CREATE INDEX IF NOT EXISTS idx_v2_imlogic_settings_user_active 
ON v2_imlogic_settings(user_id, is_active) 
WHERE is_active = true;

-- 3. 古い設定を自動的に非アクティブにする関数
CREATE OR REPLACE FUNCTION deactivate_old_imlogic_settings()
RETURNS TRIGGER AS $$
BEGIN
    -- 新規作成時のみ（更新時は除外）
    IF TG_OP = 'INSERT' THEN
        -- 同じユーザーの他の設定を非アクティブ化
        UPDATE v2_imlogic_settings 
        SET is_active = false,
            updated_at = NOW()
        WHERE user_id = NEW.user_id 
        AND id != NEW.id
        AND is_active = true;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 4. トリガーを作成
DROP TRIGGER IF EXISTS deactivate_old_imlogic_settings_trigger ON v2_imlogic_settings;
CREATE TRIGGER deactivate_old_imlogic_settings_trigger
AFTER INSERT ON v2_imlogic_settings
FOR EACH ROW
EXECUTE FUNCTION deactivate_old_imlogic_settings();

-- 5. 既存データの修正（最新のみアクティブにする）
WITH latest_settings AS (
    SELECT DISTINCT ON (user_id) 
        id,
        user_id,
        created_at
    FROM v2_imlogic_settings
    ORDER BY user_id, created_at DESC
)
UPDATE v2_imlogic_settings
SET is_active = CASE 
    WHEN id IN (SELECT id FROM latest_settings) THEN true
    ELSE false
END;

-- 6. ユーザーの現在の設定を取得するビュー（オプション）
CREATE OR REPLACE VIEW v2_user_current_imlogic_settings AS
SELECT 
    u.id as user_id,
    u.email,
    u.name,
    s.id as settings_id,
    s.settings_name,
    s.horse_weight,
    s.jockey_weight,
    s.item_weights,
    s.created_at as settings_created_at,
    s.updated_at as settings_updated_at
FROM v2_users u
LEFT JOIN v2_imlogic_settings s ON u.id = s.user_id AND s.is_active = true;

-- 7. デフォルト設定を返す関数
CREATE OR REPLACE FUNCTION get_imlogic_settings_or_default(p_user_id UUID)
RETURNS TABLE (
    id UUID,
    user_id UUID,
    settings_name VARCHAR(255),
    horse_weight INTEGER,
    jockey_weight INTEGER,
    item_weights JSONB,
    is_active BOOLEAN
) AS $$
BEGIN
    -- ユーザーのアクティブな設定を探す
    RETURN QUERY
    SELECT 
        s.id,
        s.user_id,
        s.settings_name,
        s.horse_weight,
        s.jockey_weight,
        s.item_weights,
        s.is_active
    FROM v2_imlogic_settings s
    WHERE s.user_id = p_user_id AND s.is_active = true
    LIMIT 1;
    
    -- 設定が見つからない場合はデフォルトを返す
    IF NOT FOUND THEN
        RETURN QUERY
        SELECT 
            '00000000-0000-0000-0000-000000000000'::UUID as id,
            p_user_id as user_id,
            '標準設定'::VARCHAR(255) as settings_name,
            70 as horse_weight,
            30 as jockey_weight,
            '{
                "1_distance_aptitude": 8.33,
                "2_bloodline_evaluation": 8.33,
                "3_jockey_compatibility": 8.33,
                "4_trainer_evaluation": 8.33,
                "5_track_aptitude": 8.33,
                "6_weather_aptitude": 8.33,
                "7_popularity_factor": 8.33,
                "8_weight_impact": 8.33,
                "9_horse_weight_impact": 8.33,
                "10_corner_specialist": 8.33,
                "11_margin_analysis": 8.33,
                "12_time_index": 8.37
            }'::JSONB as item_weights,
            true as is_active;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- 8. RLSポリシーの更新（必要に応じて）
-- ユーザーは自分の設定のみ参照・更新可能
DROP POLICY IF EXISTS "Users can manage own IMLogic settings" ON v2_imlogic_settings;
CREATE POLICY "Users can manage own IMLogic settings" ON v2_imlogic_settings
    FOR ALL USING (true);  -- APIレベルで制御

-- 9. コメント追加
COMMENT ON COLUMN v2_imlogic_settings.is_active IS 'ユーザーの現在アクティブな設定かどうか。1ユーザーにつき1つの設定のみがアクティブ';
COMMENT ON FUNCTION deactivate_old_imlogic_settings() IS '新しい設定が作成されたときに、古い設定を自動的に非アクティブ化する';
COMMENT ON VIEW v2_user_current_imlogic_settings IS 'ユーザーとその現在のIMLogic設定を結合したビュー';
COMMENT ON FUNCTION get_imlogic_settings_or_default(UUID) IS 'ユーザーの設定を取得し、存在しない場合はデフォルト設定を返す';