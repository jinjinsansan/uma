-- キャンペーン履歴テーブル作成
-- 作成日: 2025-09-04

-- キャンペーン履歴テーブル
CREATE TABLE IF NOT EXISTS v2_campaign_history (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    campaign_name TEXT NOT NULL,
    target_type VARCHAR(10) NOT NULL CHECK (target_type IN ('all', 'active', 'new')),
    points_granted INTEGER NOT NULL,
    users_processed INTEGER NOT NULL DEFAULT 0,
    users_failed INTEGER NOT NULL DEFAULT 0,
    executed_by TEXT NOT NULL,
    executed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- インデックス作成
CREATE INDEX IF NOT EXISTS idx_v2_campaign_history_executed_at 
ON v2_campaign_history (executed_at DESC);

CREATE INDEX IF NOT EXISTS idx_v2_campaign_history_executed_by 
ON v2_campaign_history (executed_by);

-- RLSポリシー設定（管理者のみアクセス可能）
ALTER TABLE v2_campaign_history ENABLE ROW LEVEL SECURITY;

-- 管理者のみ全てのデータにアクセス可能
CREATE POLICY "Admins can access all campaign history" 
ON v2_campaign_history 
FOR ALL 
USING (
    auth.jwt() ->> 'email' IN ('goldbenchan@gmail.com', 'kusanokiyoshi1@gmail.com')
);

-- コメント追加
COMMENT ON TABLE v2_campaign_history IS 'V2ポイントキャンペーンの実行履歴';
COMMENT ON COLUMN v2_campaign_history.campaign_name IS 'キャンペーン名・説明';
COMMENT ON COLUMN v2_campaign_history.target_type IS '対象ユーザータイプ（all: 全員, active: アクティブ, new: 新規）';
COMMENT ON COLUMN v2_campaign_history.points_granted IS '付与されたポイント数';
COMMENT ON COLUMN v2_campaign_history.users_processed IS '処理成功ユーザー数';
COMMENT ON COLUMN v2_campaign_history.users_failed IS '処理失敗ユーザー数';
COMMENT ON COLUMN v2_campaign_history.executed_by IS '実行者のメールアドレス';
COMMENT ON COLUMN v2_campaign_history.executed_at IS 'キャンペーン実行日時';