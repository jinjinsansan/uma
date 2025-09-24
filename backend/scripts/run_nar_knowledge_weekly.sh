#!/bin/bash
# -*- coding: utf-8 -*-

################################################################################
# 地方競馬ナレッジファイル自動生成スクリプト
#
# 説明:
#   毎週月曜日に実行して最新のNARデータを取得しJSONファイルを生成
#
# 実行方法:
#   手動実行: ./run_nar_knowledge_weekly.sh
#   cron設定: 0 2 * * 1 /path/to/run_nar_knowledge_weekly.sh
#             (毎週月曜日午前2時に実行)
#
################################################################################

# 設定
SCRIPT_DIR="/mnt/e/dev/Cusor/chatbot/uma/backend/scripts"
OUTPUT_DIR="/mnt/e/dev/Cusor/chatbot/uma/data/nar_knowledge"
LOG_DIR="/mnt/e/dev/Cusor/chatbot/uma/logs"
ARCHIVE_DIR="/mnt/e/dev/Cusor/chatbot/uma/data/nar_knowledge/archive"

# ディレクトリ作成
mkdir -p "$OUTPUT_DIR" "$LOG_DIR" "$ARCHIVE_DIR"

# タイムスタンプ
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DATE_TODAY=$(date +%Y-%m-%d)
LOG_FILE="$LOG_DIR/nar_knowledge_${TIMESTAMP}.log"

# ログ開始
echo "========================================" | tee -a "$LOG_FILE"
echo "地方競馬ナレッジファイル生成" | tee -a "$LOG_FILE"
echo "実行日時: $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"

# スクリプトディレクトリに移動
cd "$SCRIPT_DIR" || exit 1

# Python環境チェック
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3が見つかりません" | tee -a "$LOG_FILE"
    exit 1
fi

# PostgreSQL接続チェック
echo "データベース接続確認中..." | tee -a "$LOG_FILE"
python3 test_db_connection.py >> "$LOG_FILE" 2>&1
if [ $? -ne 0 ]; then
    echo "❌ データベース接続失敗" | tee -a "$LOG_FILE"
    exit 1
fi

# 既存ファイルをアーカイブ
if [ -f "$OUTPUT_DIR/nar_knowledge_latest.json" ]; then
    echo "既存ファイルをアーカイブ中..." | tee -a "$LOG_FILE"
    mv "$OUTPUT_DIR/nar_knowledge_latest.json" \
       "$ARCHIVE_DIR/nar_knowledge_backup_${TIMESTAMP}.json"
fi

# メインスクリプト実行
echo "ナレッジファイル生成開始..." | tee -a "$LOG_FILE"
python3 create_nar_horse_knowledge_v9_perfect_base.py >> "$LOG_FILE" 2>&1

if [ $? -eq 0 ]; then
    # 生成されたファイルを探す
    GENERATED_FILE=$(ls -t nar_knowledge_*.json 2>/dev/null | head -1)

    if [ -n "$GENERATED_FILE" ]; then
        # ファイルを正しい場所に移動
        mv "$GENERATED_FILE" "$OUTPUT_DIR/nar_knowledge_latest.json"

        # 成功メッセージ
        echo "✅ 生成成功" | tee -a "$LOG_FILE"
        echo "   ファイル: $OUTPUT_DIR/nar_knowledge_latest.json" | tee -a "$LOG_FILE"

        # ファイルサイズ確認
        FILE_SIZE=$(ls -lh "$OUTPUT_DIR/nar_knowledge_latest.json" | awk '{print $5}')
        echo "   サイズ: $FILE_SIZE" | tee -a "$LOG_FILE"

        # 統計情報を出力
        echo "" | tee -a "$LOG_FILE"
        echo "統計情報:" | tee -a "$LOG_FILE"
        python3 -c "
import json
with open('$OUTPUT_DIR/nar_knowledge_latest.json', 'r') as f:
    data = json.load(f)
    print(f'   馬数: {len(data):,}頭')
    total_races = sum(d['total_races'] for d in data.values())
    print(f'   総レース数: {total_races:,}')
        " | tee -a "$LOG_FILE"

        # 古いアーカイブを削除（30日以上前）
        echo "" | tee -a "$LOG_FILE"
        echo "古いアーカイブを削除中..." | tee -a "$LOG_FILE"
        find "$ARCHIVE_DIR" -name "nar_knowledge_backup_*.json" \
             -mtime +30 -delete 2>/dev/null

        EXIT_CODE=0
    else
        echo "❌ 生成ファイルが見つかりません" | tee -a "$LOG_FILE"
        EXIT_CODE=1
    fi
else
    echo "❌ 生成失敗" | tee -a "$LOG_FILE"
    EXIT_CODE=1
fi

# 完了
echo "" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"
echo "処理完了: $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"

exit $EXIT_CODE