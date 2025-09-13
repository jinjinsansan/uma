-- MetaLogicをv2_chat_messagesテーブルに追加するためのSQL
-- 実行日: 2025-09-13
-- 目的: MetaLogic（メタ予想システム）をV2チャットで使用可能にする

-- 1. 現在の制約を確認
SELECT conname, pg_get_constraintdef(oid)
FROM pg_constraint
WHERE conname = 'v2_chat_messages_ai_type_check';

-- 2. 既存の制約を削除
ALTER TABLE v2_chat_messages
DROP CONSTRAINT v2_chat_messages_ai_type_check;

-- 3. 新しい制約を追加（metalogicを含む）
ALTER TABLE v2_chat_messages
ADD CONSTRAINT v2_chat_messages_ai_type_check
CHECK (ai_type IN ('dlogic', 'ilogic', 'imlogic', 'viewlogic', 'flogic', 'metalogic'));

-- 4. 変更の確認
SELECT conname, pg_get_constraintdef(oid)
FROM pg_constraint
WHERE conname = 'v2_chat_messages_ai_type_check';