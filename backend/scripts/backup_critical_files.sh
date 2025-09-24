#!/bin/bash
# 地方競馬NAR重要ファイルバックアップスクリプト
# 実行日: $(date +%Y-%m-%d)

BACKUP_DIR="/mnt/e/dev/Cusor/chatbot/uma/BACKUP_NAR_$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

echo "🔒 重要ファイルをバックアップ中..."

# スケジュールマスター（最重要）
cp -v /mnt/e/dev/Cusor/chatbot/uma/data/nankan_schedule_master_2019_2025.json "$BACKUP_DIR/"

# SDKツール
cp -v /mnt/e/dev/Cusor/chatbot/uma/backend/scripts/create_nar_horse_knowledge_v9_perfect_base.py "$BACKUP_DIR/"

# スケジュール追加スクリプト
cp -v /mnt/e/dev/Cusor/chatbot/uma/backend/scripts/add_2019_schedule.py "$BACKUP_DIR/"
cp -v /mnt/e/dev/Cusor/chatbot/uma/backend/scripts/add_2020_schedule.py "$BACKUP_DIR/"
cp -v /mnt/e/dev/Cusor/chatbot/uma/backend/scripts/add_2021_schedule.py "$BACKUP_DIR/"
cp -v /mnt/e/dev/Cusor/chatbot/uma/backend/scripts/add_2022_schedule.py "$BACKUP_DIR/"

# マニュアル
cp -v /mnt/e/dev/Cusor/chatbot/uma/backend/scripts/NAR_WEEKLY_UPDATE_MANUAL.md "$BACKUP_DIR/"

# 最新ナレッジファイル（存在する場合）
if [ -f /mnt/e/dev/Cusor/chatbot/uma/backend/scripts/nankan_unified_knowledge_20250907.json ]; then
    cp -v /mnt/e/dev/Cusor/chatbot/uma/backend/scripts/nankan_unified_knowledge_20250907.json "$BACKUP_DIR/"
fi

echo "✅ バックアップ完了！"
echo "📂 保存先: $BACKUP_DIR"
ls -lh "$BACKUP_DIR/"