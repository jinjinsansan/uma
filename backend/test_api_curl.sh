#!/bin/bash

# Logic Chat V2 API テストスクリプト
echo "🚀 Logic Chat V2 API テスト開始"
echo "========================================"

# ベースURL
BASE_URL="http://localhost:8001"

# テスト用変数
CHAT_ID=""
SETTINGS_ID=""

# 色付き出力用
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: ヘルスチェック
echo -e "\n${YELLOW}Step 1: ヘルスチェック${NC}"
echo "----------------------------------------"
curl -s -X GET "${BASE_URL}/" | python3 -m json.tool

# Step 2: プリセット一覧の取得
echo -e "\n\n${YELLOW}Step 2: プリセット一覧の取得${NC}"
echo "----------------------------------------"
PRESETS_RESPONSE=$(curl -s -X GET "${BASE_URL}/api/v2/imlogic-settings/presets/list")
echo "$PRESETS_RESPONSE" | python3 -m json.tool

# Step 3: IMLogic設定の作成（血統重視型）
echo -e "\n\n${YELLOW}Step 3: IMLogic設定の作成（血統重視型）${NC}"
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
echo -e "${GREEN}✅ 設定ID: $SETTINGS_ID${NC}"

# Step 4: レース固定チャットの作成
echo -e "\n\n${YELLOW}Step 4: レース固定チャットの作成${NC}"
echo "----------------------------------------"
CHAT_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/v2/logic-chat/create" \
  -H "Content-Type: application/json" \
  -d '{
    "race_id": "test-tokyo-11r-20250111",
    "race_date": "2025-01-11",
    "venue": "東京",
    "race_number": 11,
    "race_name": "テスト記念（G2）",
    "horses": ["イクイノックス", "ドウデュース", "リバティアイランド", "ソダシ"],
    "jockeys": ["C.ルメール", "武豊", "川田将雅", "吉田隼人"],
    "posts": [1, 2, 3, 4],
    "horse_numbers": [1, 2, 3, 4]
  }')

echo "$CHAT_RESPONSE" | python3 -m json.tool
CHAT_ID=$(echo "$CHAT_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['chat_id'])")
echo -e "${GREEN}✅ チャットID: $CHAT_ID${NC}"

# Step 5: IMLogic分析（デフォルト設定）
echo -e "\n\n${YELLOW}Step 5: IMLogic分析（デフォルト設定）${NC}"
echo "----------------------------------------"
ANALYSIS_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/v2/logic-chat/analyze" \
  -H "Content-Type: application/json" \
  -d "{
    \"chat_id\": \"$CHAT_ID\",
    \"engine_type\": \"imlogic\",
    \"imlogic_settings_id\": \"default\",
    \"message\": \"全馬分析して\"
  }")

echo "$ANALYSIS_RESPONSE" | python3 -m json.tool | head -50
echo "... (結果省略)"

# Step 6: IMLogic分析（カスタム設定）
echo -e "\n\n${YELLOW}Step 6: IMLogic分析（血統重視カスタム）${NC}"
echo "----------------------------------------"
CUSTOM_ANALYSIS=$(curl -s -X POST "${BASE_URL}/api/v2/logic-chat/analyze" \
  -H "Content-Type: application/json" \
  -d "{
    \"chat_id\": \"$CHAT_ID\",
    \"engine_type\": \"imlogic\",
    \"imlogic_settings_id\": \"$SETTINGS_ID\",
    \"message\": \"血統重視で分析して\"
  }")

echo "$CUSTOM_ANALYSIS" | python3 -m json.tool | head -50
echo "... (結果省略)"

# Step 7: エラーケーステスト
echo -e "\n\n${YELLOW}Step 7: エラーケーステスト${NC}"
echo "========================================"

# 7-1: 無効な馬名
echo -e "\n${YELLOW}7-1: 無効な馬名での分析${NC}"
echo "----------------------------------------"
ERROR_TEST1=$(curl -s -X POST "${BASE_URL}/api/v2/logic-chat/analyze" \
  -H "Content-Type: application/json" \
  -d "{
    \"chat_id\": \"$CHAT_ID\",
    \"engine_type\": \"imlogic\",
    \"imlogic_settings_id\": \"default\",
    \"message\": \"存在しない馬を分析して\"
  }")

echo "$ERROR_TEST1" | python3 -m json.tool | head -20

# 7-2: 重みの合計が100でない
echo -e "\n${YELLOW}7-2: 重みの合計が100でない設定${NC}"
echo "----------------------------------------"
INVALID_SETTINGS=$(curl -s -X POST "${BASE_URL}/api/v2/imlogic-settings/create" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "無効な設定",
    "horse_weight": 60,
    "jockey_weight": 60,
    "item_weights": {
      "1_distance_aptitude": 10.0,
      "2_bloodline_evaluation": 10.0,
      "3_jockey_compatibility": 10.0,
      "4_trainer_evaluation": 10.0,
      "5_track_aptitude": 10.0,
      "6_weather_aptitude": 10.0,
      "7_popularity_factor": 10.0,
      "8_weight_impact": 10.0,
      "9_horse_weight_impact": 10.0,
      "10_corner_specialist": 10.0,
      "11_margin_analysis": 10.0,
      "12_time_index": 10.0
    }
  }')

echo "$INVALID_SETTINGS" | python3 -m json.tool

echo -e "\n\n${GREEN}🎉 Logic Chat V2 API テスト完了！${NC}"
echo "========================================"