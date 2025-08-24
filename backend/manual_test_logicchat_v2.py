"""
Logic Chat V2 手動テストスクリプト
requestsライブラリを使用したシンプルなテスト
"""
import requests
import json
from datetime import datetime

# テスト用のベースURL
BASE_URL = "http://localhost:8001"

print("🚀 Logic Chat V2 手動テスト開始")
print("=" * 80)

try:
    # Step 1: ヘルスチェック
    print("\n🏥 ヘルスチェック")
    print("-" * 40)
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"❌ サーバーに接続できません: {e}")
        print("サーバーが起動していることを確認してください")
        exit(1)

    # Step 2: プリセット一覧の取得
    print("\n\n📋 プリセット一覧の取得")
    print("-" * 40)
    response = requests.get(f"{BASE_URL}/api/v2/imlogic-settings/presets/list")
    if response.status_code == 200:
        presets = response.json()
        print(f"✅ {len(presets['presets'])}個のプリセットを取得")
        for preset in presets['presets']:
            print(f"   - {preset['name']}: {preset['description']}")
    else:
        print(f"❌ エラー: {response.status_code}")
        print(response.text)

    # Step 3: IMLogic設定の作成
    print("\n\n📝 IMLogic設定の作成（血統重視型）")
    print("-" * 40)
    settings_data = {
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
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v2/imlogic-settings/create",
        json=settings_data
    )
    
    if response.status_code == 200:
        result = response.json()
        settings_id = result["id"]
        print(f"✅ 設定作成成功")
        print(f"   設定ID: {settings_id}")
        print(f"   設定名: {result['settings']['name']}")
    else:
        print(f"❌ エラー: {response.status_code}")
        print(response.text)
        settings_id = None

    # Step 4: レース固定チャットの作成
    print("\n\n💬 レース固定チャットの作成")
    print("-" * 40)
    race_data = {
        "race_id": "test-tokyo-11r-20250111",
        "race_date": "2025-01-11",
        "venue": "東京",
        "race_number": 11,
        "race_name": "テスト記念（G2）",
        "horses": ["イクイノックス", "ドウデュース", "リバティアイランド", "ソダシ"],
        "jockeys": ["C.ルメール", "武豊", "川田将雅", "吉田隼人"],
        "posts": [1, 2, 3, 4],
        "horse_numbers": [1, 2, 3, 4]
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v2/logic-chat/create",
        json=race_data
    )
    
    if response.status_code == 200:
        result = response.json()
        chat_id = result["chat_id"]
        print(f"✅ チャット作成成功")
        print(f"   チャットID: {chat_id}")
        print(f"   レース: {result['race_data']['venue']} {result['race_data']['race_number']}R")
    else:
        print(f"❌ エラー: {response.status_code}")
        print(response.text)
        chat_id = None

    # Step 5: IMLogic分析（デフォルト設定）
    if chat_id:
        print("\n\n🔍 IMLogic分析（デフォルト設定）")
        print("-" * 40)
        analysis_request = {
            "chat_id": chat_id,
            "engine_type": "imlogic",
            "imlogic_settings_id": "default",
            "message": "全馬分析して"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v2/logic-chat/analyze",
            json=analysis_request
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 分析成功")
            if 'analysis_result' in result and 'results' in result['analysis_result']:
                results = result['analysis_result']['results']
                print("\n上位3頭:")
                for horse in results[:3]:
                    print(f"  {horse['rank']}位: {horse['horse']} ({horse['total_score']}点)")
        else:
            print(f"❌ エラー: {response.status_code}")
            print(response.text)

    # Step 6: エラーケーステスト
    print("\n\n⚠️ エラーケーステスト")
    print("-" * 40)
    
    # 無効な馬名
    if chat_id:
        print("\n1️⃣ 無効な馬名での分析")
        analysis_request = {
            "chat_id": chat_id,
            "engine_type": "imlogic",
            "imlogic_settings_id": "default",
            "message": "「存在しない馬」を分析して"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v2/logic-chat/analyze",
            json=analysis_request
        )
        
        if response.status_code == 400:
            print("✅ 期待通りエラーを返却")
            print(f"   エラー: {response.json()['detail']}")
        else:
            print(f"❌ 予期しないレスポンス: {response.status_code}")

    # 重みの合計が100でない
    print("\n2️⃣ 重みの合計が100でない設定")
    invalid_settings = {
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
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v2/imlogic-settings/create",
        json=invalid_settings
    )
    
    if response.status_code == 400:
        print("✅ 期待通りバリデーションエラー")
        print(f"   エラー: {response.json()['detail']}")
    else:
        print(f"❌ 予期しないレスポンス: {response.status_code}")

    print("\n\n✅ テスト完了！")

except requests.exceptions.ConnectionError:
    print("\n❌ サーバーに接続できません")
    print("以下のコマンドでサーバーを起動してください:")
    print("cd /mnt/c/Users/USER/OneDrive/デスクトップ/Cusor/chatbot/uma/backend")
    print("python3 -m uvicorn main:app --reload --port 8000")
    
except Exception as e:
    print(f"\n❌ エラー: {e}")
    import traceback
    traceback.print_exc()