-- V2システム用の独立したユーザーテーブル作成
-- 既存の2500ユーザーには一切影響しません

-- 1. V2専用ユーザーテーブルを作成
CREATE TABLE v2_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    google_id TEXT UNIQUE,
    avatar_url TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 2. V2ユーザーテーブルのインデックス作成（パフォーマンス向上）
CREATE INDEX idx_v2_users_email ON v2_users(email);
CREATE INDEX idx_v2_users_google_id ON v2_users(google_id);

-- 3. v2_user_pointsテーブルの外部キー制約を削除
ALTER TABLE v2_user_points 
DROP CONSTRAINT IF EXISTS v2_user_points_user_id_fkey;

-- 4. v2_user_pointsテーブルの外部キーをv2_usersテーブルに変更
ALTER TABLE v2_user_points 
ADD CONSTRAINT v2_user_points_user_id_fkey 
FOREIGN KEY (user_id) REFERENCES v2_users(id) ON DELETE CASCADE;

-- 5. v2_chat_sessionsテーブルの外部キー制約も更新（もし存在する場合）
ALTER TABLE v2_chat_sessions 
DROP CONSTRAINT IF EXISTS v2_chat_sessions_user_id_fkey;

ALTER TABLE v2_chat_sessions 
ADD CONSTRAINT v2_chat_sessions_user_id_fkey 
FOREIGN KEY (user_id) REFERENCES v2_users(id) ON DELETE CASCADE;

-- 6. v2_point_transactionsテーブルの外部キー制約も更新（もし存在する場合）
ALTER TABLE v2_point_transactions 
DROP CONSTRAINT IF EXISTS v2_point_transactions_user_id_fkey;

ALTER TABLE v2_point_transactions 
ADD CONSTRAINT v2_point_transactions_user_id_fkey 
FOREIGN KEY (user_id) REFERENCES v2_users(id) ON DELETE CASCADE;

-- 7. RLS（Row Level Security）を有効化
ALTER TABLE v2_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE v2_user_points ENABLE ROW LEVEL SECURITY;
ALTER TABLE v2_chat_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE v2_point_transactions ENABLE ROW LEVEL SECURITY;

-- 8. 基本的なRLSポリシーを作成（開発用）
-- ユーザーは自分のデータのみアクセス可能
CREATE POLICY "Users can view own data" ON v2_users
    FOR SELECT USING (auth.uid()::text = id::text);

CREATE POLICY "Users can update own data" ON v2_users
    FOR UPDATE USING (auth.uid()::text = id::text);

-- サービスロールは全アクセス可能（バックエンド用）
CREATE POLICY "Service role has full access" ON v2_users
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role has full access to points" ON v2_user_points
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role has full access to chats" ON v2_chat_sessions
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role has full access to transactions" ON v2_point_transactions
    FOR ALL USING (auth.role() = 'service_role');

-- 9. 更新日時の自動更新トリガー
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_v2_users_updated_at BEFORE UPDATE
    ON v2_users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 実行完了メッセージ
-- すべてのコマンドが成功すれば、V2専用のユーザー管理システムが完成します
-- 既存の'users'テーブルには一切影響しません