#!/bin/bash

# Logic Chat V2 API テストスクリプト
# curlを使用した実際のAPIエンドポイントテスト

BASE_URL="http://localhost:8000"
echo "🚀 Logic Chat V2 API テスト開始"
echo "========================================"

# 変数定義
CHAT_ID=""
SETTINGS_ID=""

# Step 1: プリセット一覧の取得
echo -e "\n📋 Step 1: プリセット一覧の取得"
echo "----------------------------------------"
curl -X GET "${BASE_URL}/api/v2/imlogic-settings/presets/list" \
  -H "Content-Type: application/json" | python3 -m json.tool

# Step 2: IMLogic設定の作成
echo -e "\n\n📝 Step 2: IMLogic設定の作成（血統重視型）"
echo "----------------------------------------"
SETTINGS_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/v2/imlogic-settings/create" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "血統重視カスタム",
    "horse_weight": 80,
    "jockey_weight": 20,
    "item_weights": {
      "1_distance_aptitude": 5.0,
      "2_bloodline_evaluation": 40.0,
      "3_jockey_compatibility": 5.0,
      "4_trainer_evaluation": 5.0,
      "5_track_aptitude": 5.0,
      "6_weather_aptitude": 5.0,
      "7_popularity_factor": 5.0,
      "8_weight_impact": 5.0,
      "9_horse_weight_impact": 5.0,
      "10_corner_specialist": 5.0,
      "11_margin_analysis": 5.0,
      "12_time_index": 10.0
    }
  }')

echo "$SETTINGS_RESPONSE" | python3 -m json.tool
SETTINGS_ID=$(echo "$SETTINGS_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
echo "✅ 設定ID: $SETTINGS_ID"

# Step 3: レース固定チャットの作成
echo -e "\n\n💬 Step 3: レース固定チャットの作成"
echo "----------------------------------------"
CHAT_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/v2/logic-chat/create" \
  -H "Content-Type: application/json" \
  -d '{
    "race_id": "test-tokyo-11r-20250111",
    "race_date": "2025-01-11",
    "venue": "東京",
    "race_number": 11,
    "race_name": "テスト記念（G2）",
    "horses": ["イクイノックス", "ドウデュース", "リバティアイランド", "ソダシ", "ジャスティンパレス", "タイトルホルダー"],
    "jockeys": ["C.ルメール", "武豊", "川田将雅", "吉田隼人", "横山和生", "横山武史"],
    "posts": [1, 2, 3, 4, 5, 6],
    "horse_numbers": [1, 2, 3, 4, 5, 6]
  }')

echo "$CHAT_RESPONSE" | python3 -m json.tool
CHAT_ID=$(echo "$CHAT_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['chat_id'])")
echo "✅ チャットID: $CHAT_ID"

# Step 4: IMLogic分析（デフォルト設定）
echo -e "\n\n🔍 Step 4: IMLogic分析（デフォルト設定）"
echo "----------------------------------------"
curl -s -X POST "${BASE_URL}/api/v2/logic-chat/analyze" \
  -H "Content-Type: application/json" \
  -d "{
    \"chat_id\": \"$CHAT_ID\",
    \"engine_type\": \"imlogic\",
    \"imlogic_settings_id\": \"default\",
    \"message\": \"全馬分析して\"
  }" | python3 -m json.tool

# Step 5: IMLogic分析（カスタム設定）
echo -e "\n\n🔍 Step 5: IMLogic分析（血統重視カスタム）"
echo "----------------------------------------"
curl -s -X POST "${BASE_URL}/api/v2/logic-chat/analyze" \
  -H "Content-Type: application/json" \
  -d "{
    \"chat_id\": \"$CHAT_ID\",
    \"engine_type\": \"imlogic\",
    \"imlogic_settings_id\": \"$SETTINGS_ID\",
    \"message\": \"血統重視で分析して\"
  }" | python3 -m json.tool

# Step 6: 設定の更新（騎手重視に変更）
echo -e "\n\n🔄 Step 6: IMLogic設定の更新（騎手重視に変更）"
echo "----------------------------------------"
curl -s -X PUT "${BASE_URL}/api/v2/imlogic-settings/${SETTINGS_ID}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "騎手重視に変更",
    "horse_weight": 50,
    "jockey_weight": 50,
    "item_weights": {
      "1_distance_aptitude": 8.0,
      "2_bloodline_evaluation": 5.0,
      "3_jockey_compatibility": 25.0,
      "4_trainer_evaluation": 8.0,
      "5_track_aptitude": 8.0,
      "6_weather_aptitude": 5.0,
      "7_popularity_factor": 5.0,
      "8_weight_impact": 5.0,
      "9_horse_weight_impact": 5.0,
      "10_corner_specialist": 8.0,
      "11_margin_analysis": 8.0,
      "12_time_index": 10.0
    }
  }' | python3 -m json.tool

# Step 7: 更新後の分析
echo -e "\n\n🔍 Step 7: 更新後の分析（騎手重視）"
echo "----------------------------------------"
curl -s -X POST "${BASE_URL}/api/v2/logic-chat/analyze" \
  -H "Content-Type: application/json" \
  -d "{
    \"chat_id\": \"$CHAT_ID\",
    \"engine_type\": \"imlogic\",
    \"imlogic_settings_id\": \"$SETTINGS_ID\",
    \"message\": \"騎手重視で再分析\"
  }" | python3 -m json.tool

# Step 8: チャット履歴の確認
echo -e "\n\n📜 Step 8: チャット履歴の確認"
echo "----------------------------------------"
curl -s -X GET "${BASE_URL}/api/v2/logic-chat/chat/${CHAT_ID}" \
  -H "Content-Type: application/json" | python3 -m json.tool

# Step 9: ViewLogic分析（開発中）
echo -e "\n\n👁️ Step 9: ViewLogic分析（開発中）"
echo "----------------------------------------"
curl -s -X POST "${BASE_URL}/api/v2/logic-chat/analyze" \
  -H "Content-Type: application/json" \
  -d "{
    \"chat_id\": \"$CHAT_ID\",
    \"engine_type\": \"viewlogic\",
    \"message\": \"レースの傾向を分析して\"
  }" | python3 -m json.tool

# エラーケーステスト
echo -e "\n\n⚠️ エラーケーステスト"
echo "========================================"

# 1. 無効な馬名での分析
echo -e "\n1️⃣ 無効な馬名での分析テスト"
echo "----------------------------------------"
curl -s -X POST "${BASE_URL}/api/v2/logic-chat/analyze" \
  -H "Content-Type: application/json" \
  -d "{
    \"chat_id\": \"$CHAT_ID\",
    \"engine_type\": \"imlogic\",
    \"imlogic_settings_id\": \"default\",
    \"message\": \"「存在しない馬」を分析して\"
  }" | python3 -m json.tool

# 2. 無効な設定IDでの分析
echo -e "\n\n2️⃣ 無効な設定IDでの分析テスト"
echo "----------------------------------------"
curl -s -X POST "${BASE_URL}/api/v2/logic-chat/analyze" \
  -H "Content-Type: application/json" \
  -d "{
    \"chat_id\": \"$CHAT_ID\",
    \"engine_type\": \"imlogic\",
    \"imlogic_settings_id\": \"invalid-settings-id\",
    \"message\": \"分析して\"
  }" | python3 -m json.tool

# 3. 重みの合計が100でない設定
echo -e "\n\n3️⃣ 重みの合計が100でない設定テスト"
echo "----------------------------------------"
curl -s -X POST "${BASE_URL}/api/v2/imlogic-settings/create" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "無効な設定",
    "horse_weight": 60,
    "jockey_weight": 60,
    "item_weights": {}
  }' | python3 -m json.tool

echo -e "\n\n🎉 Logic Chat V2 API テスト完了！"
echo "========================================"