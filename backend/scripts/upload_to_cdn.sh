#!/bin/bash
# CDNへのアップロードスクリプト

echo "🚀 Cloudflare R2へのアップロード準備"

# ファイルサイズ確認
FILE_SIZE=$(ls -lh nankan_unified_knowledge_20250907.json | awk '{print $5}')
echo "📊 ファイルサイズ: $FILE_SIZE"

# バックアップ作成
cp nankan_unified_knowledge_20250907.json nankan_unified_knowledge_20250907_backup_$(date +%Y%m%d_%H%M%S).json
echo "✅ バックアップ作成完了"

# アップロードコマンド（実際の認証情報は環境変数から取得）
echo ""
echo "以下のコマンドでCDNにアップロード:"
echo "aws s3 cp nankan_unified_knowledge_20250907.json s3://your-bucket/nankan_unified_knowledge_20250907.json --endpoint-url https://YOUR_ACCOUNT_ID.r2.cloudflarestorage.com"
echo ""
echo "または、rcloneを使用:"
echo "rclone copy nankan_unified_knowledge_20250907.json r2:your-bucket/"

# 検証用URL
echo ""
echo "📍 アップロード後の確認URL:"
echo "https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/nankan_unified_knowledge_20250907.json"