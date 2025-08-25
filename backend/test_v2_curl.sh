#!/bin/bash

# V2 API curlテストスクリプト

# 設定
BASE_URL="http://localhost:8000"
# BASE_URL="https://uma-i30n.onrender.com"
TEST_EMAIL="test@example.com"

echo "=================================="
echo "V2 API テスト"
echo "URL: $BASE_URL"
echo "=================================="

echo ""
echo "1. ヘルスチェック"
echo "-----------------"
curl -X GET "$BASE_URL/api/v2/health/" | jq '.'

echo ""
echo "2. ポイント状態確認"
echo "-------------------"
curl -X GET "$BASE_URL/api/v2/points/status" \
  -H "Authorization: Bearer $TEST_EMAIL" | jq '.'

echo ""
echo "3. チャット作成"
echo "---------------"
CHAT_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v2/chat/create" \
  -H "Authorization: Bearer $TEST_EMAIL" \
  -H "Content-Type: application/json" \
  -d '{
    "race_id": "test-race-20250824",
    "race_date": "2025-08-24",
    "venue": "東京",
    "race_number": 11,
    "race_name": "テストレース",
    "horses": ["ドウデュース", "イクイノックス", "リバティアイランド"],
    "jockeys": ["武豊", "C.ルメール", "川田将雅"],
    "posts": [1, 2, 3],
    "horse_numbers": [1, 2, 3]
  }')

echo "$CHAT_RESPONSE" | jq '.'
CHAT_ID=$(echo "$CHAT_RESPONSE" | jq -r '.chat_id')

echo ""
echo "4. チャットセッション一覧"
echo "-------------------------"
curl -X GET "$BASE_URL/api/v2/chat/sessions" \
  -H "Authorization: Bearer $TEST_EMAIL" | jq '.'

if [ ! -z "$CHAT_ID" ] && [ "$CHAT_ID" != "null" ]; then
  echo ""
  echo "5. メッセージ送信"
  echo "-----------------"
  curl -X POST "$BASE_URL/api/v2/chat/session/$CHAT_ID/message" \
    -H "Authorization: Bearer $TEST_EMAIL" \
    -H "Content-Type: application/json" \
    -d '{
      "message": "このレースを分析してください",
      "ai_type": "imlogic"
    }' | jq '.'
fi

echo ""
echo "テスト完了"