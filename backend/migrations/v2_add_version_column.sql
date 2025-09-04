-- V2システム 楽観的ロック用のversion列追加
-- 実行日: 2025-09-04
-- 目的: 同時実行制御による二重消費防止

-- 1. v2_user_pointsテーブルにversion列を追加
-- 既存データは全てversion=0から開始
ALTER TABLE v2_user_points 
ADD COLUMN IF NOT EXISTS version INTEGER DEFAULT 0;

-- 2. 既存データのversion初期化（念のため）
UPDATE v2_user_points 
SET version = 0 
WHERE version IS NULL;

-- 3. version列にNOT NULL制約を追加
ALTER TABLE v2_user_points 
ALTER COLUMN version SET NOT NULL;

-- 4. パフォーマンス改善用インデックス作成

-- コラム閲覧済みチェック用インデックス
CREATE INDEX IF NOT EXISTS idx_v2_column_reads_user_column 
ON v2_column_reads(user_id, column_id);

-- ポイント履歴取得用インデックス（ユーザーID + 作成日時の降順）
CREATE INDEX IF NOT EXISTS idx_v2_point_transactions_user_created 
ON v2_point_transactions(user_id, created_at DESC);

-- コラムビュー集計用インデックス
CREATE INDEX IF NOT EXISTS idx_v2_column_views_column_created
ON v2_column_views(column_id, viewed_at DESC);

-- 5. 確認用クエリ
-- 以下のクエリで変更が正しく適用されたか確認
-- SELECT column_name, data_type, is_nullable, column_default 
-- FROM information_schema.columns 
-- WHERE table_name = 'v2_user_points' 
-- AND column_name = 'version';

-- 6. ロールバック用（必要な場合のみ）
-- ALTER TABLE v2_user_points DROP COLUMN IF EXISTS version;
-- DROP INDEX IF EXISTS idx_v2_column_reads_user_column;
-- DROP INDEX IF EXISTS idx_v2_point_transactions_user_created;
-- DROP INDEX IF EXISTS idx_v2_column_views_column_created;