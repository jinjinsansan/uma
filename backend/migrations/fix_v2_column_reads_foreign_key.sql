-- v2_column_readsテーブルの外部キー制約を修正するSQL
-- 作成日: 2025-09-04

-- 現在の外部キー制約を確認
SELECT 
    conname AS constraint_name,
    conrelid::regclass AS table_name,
    confrelid::regclass AS referenced_table
FROM 
    pg_constraint
WHERE 
    conrelid = 'v2_column_reads'::regclass
    AND contype = 'f';

-- 既存の外部キー制約を削除（制約名が判明したら実行）
-- ALTER TABLE v2_column_reads DROP CONSTRAINT IF EXISTS v2_column_reads_column_id_fkey;

-- v2_columnsテーブルへの新しい外部キー制約を追加
-- ALTER TABLE v2_column_reads 
-- ADD CONSTRAINT v2_column_reads_column_id_fkey 
-- FOREIGN KEY (column_id) REFERENCES v2_columns(id) ON DELETE CASCADE;