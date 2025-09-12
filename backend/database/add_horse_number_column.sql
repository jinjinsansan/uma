-- jra_horsesテーブルに馬番カラムを追加
ALTER TABLE jra_horses 
ADD COLUMN IF NOT EXISTS 馬番 INTEGER;

-- インデックスを追加（検索性能向上）
CREATE INDEX IF NOT EXISTS idx_jra_horses_number ON jra_horses(馬番);