-- V2 キーワードキャンペーン機能のテーブル作成
-- 作成日: 2025-09-04
-- 目的: 動画配信等でキーワードを伝え、ユーザーが入力するとポイント付与

-- 1. キーワードキャンペーンマスターテーブル
CREATE TABLE IF NOT EXISTS v2_campaign_keywords (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  keyword VARCHAR(100) NOT NULL UNIQUE, -- カタカナのキーワード（ユニーク制約）
  campaign_name VARCHAR(255) NOT NULL, -- キャンペーン名（例：「年末特別配信キャンペーン」）
  description TEXT, -- キャンペーンの説明
  points INTEGER NOT NULL CHECK (points > 0), -- 付与ポイント数（正の値のみ）
  valid_from TIMESTAMP WITH TIME ZONE NOT NULL, -- 有効期限開始
  valid_until TIMESTAMP WITH TIME ZONE NOT NULL, -- 有効期限終了
  max_uses INTEGER, -- 最大使用回数（NULL = 無制限）
  current_uses INTEGER DEFAULT 0, -- 現在の使用回数
  is_active BOOLEAN DEFAULT true, -- 有効/無効フラグ
  created_by UUID REFERENCES v2_users(id), -- 作成した管理者
  created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
  
  -- 有効期限の整合性チェック
  CONSTRAINT valid_period_check CHECK (valid_from < valid_until),
  -- 使用回数の整合性チェック
  CONSTRAINT usage_check CHECK (
    max_uses IS NULL OR 
    (max_uses > 0 AND current_uses >= 0 AND current_uses <= max_uses)
  )
);

-- 2. キーワード使用履歴テーブル（重複防止）
CREATE TABLE IF NOT EXISTS v2_keyword_redemptions (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  keyword_id UUID NOT NULL REFERENCES v2_campaign_keywords(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES v2_users(id) ON DELETE CASCADE,
  points_granted INTEGER NOT NULL CHECK (points_granted > 0),
  redeemed_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
  ip_address INET, -- 不正利用監視用
  user_agent TEXT, -- 不正利用監視用
  
  -- 1ユーザー1キーワード1回の制約
  UNIQUE(keyword_id, user_id)
);

-- 3. パフォーマンス向上のためのインデックス
CREATE INDEX idx_v2_campaign_keywords_active 
  ON v2_campaign_keywords(is_active, valid_from, valid_until) 
  WHERE is_active = true;

CREATE INDEX idx_v2_campaign_keywords_keyword 
  ON v2_campaign_keywords(keyword) 
  WHERE is_active = true;

CREATE INDEX idx_v2_keyword_redemptions_user 
  ON v2_keyword_redemptions(user_id);

CREATE INDEX idx_v2_keyword_redemptions_keyword 
  ON v2_keyword_redemptions(keyword_id);

CREATE INDEX idx_v2_keyword_redemptions_redeemed 
  ON v2_keyword_redemptions(redeemed_at DESC);

-- 4. 更新日時自動更新トリガー
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = TIMEZONE('utc', NOW());
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_v2_campaign_keywords_updated_at 
  BEFORE UPDATE ON v2_campaign_keywords 
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 5. 使用回数自動更新トリガー
CREATE OR REPLACE FUNCTION increment_keyword_usage()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE v2_campaign_keywords 
    SET current_uses = current_uses + 1 
    WHERE id = NEW.keyword_id;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER increment_keyword_usage_trigger 
  AFTER INSERT ON v2_keyword_redemptions 
  FOR EACH ROW EXECUTE FUNCTION increment_keyword_usage();

-- 6. 権限設定
GRANT SELECT, INSERT, UPDATE ON v2_campaign_keywords TO authenticated;
GRANT SELECT, INSERT ON v2_keyword_redemptions TO authenticated;
GRANT ALL ON v2_campaign_keywords TO service_role;
GRANT ALL ON v2_keyword_redemptions TO service_role;

-- 7. RLS（Row Level Security）設定
ALTER TABLE v2_campaign_keywords ENABLE ROW LEVEL SECURITY;
ALTER TABLE v2_keyword_redemptions ENABLE ROW LEVEL SECURITY;

-- 管理者のみキャンペーン作成・編集可能
CREATE POLICY admin_manage_keywords ON v2_campaign_keywords
  FOR ALL 
  TO authenticated
  USING (
    auth.uid() IN (
      SELECT id FROM v2_users 
      WHERE role = 'admin'
    )
  );

-- ユーザーは自分の履歴のみ参照可能
CREATE POLICY users_view_own_redemptions ON v2_keyword_redemptions
  FOR SELECT 
  TO authenticated
  USING (auth.uid() = user_id);

-- 8. サンプルデータ（開発用、本番では削除）
-- INSERT INTO v2_campaign_keywords (
--   keyword, 
--   campaign_name, 
--   description, 
--   points, 
--   valid_from, 
--   valid_until, 
--   max_uses
-- ) VALUES (
--   'スペシャルボーナス2024', 
--   'テスト配信キャンペーン', 
--   'テスト用のキャンペーンです', 
--   10, 
--   NOW(), 
--   NOW() + INTERVAL '7 days', 
--   100
-- );

-- 確認用クエリ
-- SELECT * FROM v2_campaign_keywords;
-- SELECT * FROM v2_keyword_redemptions;