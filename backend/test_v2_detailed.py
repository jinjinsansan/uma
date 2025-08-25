"""
V2 API 詳細テストスクリプト
各ステップを確認しながら実行
"""
import requests
import json
import sys

# テスト設定
BASE_URL = "http://localhost:8000"
TEST_EMAIL = "test-v2@example.com"  # 新しいテストユーザー

print("V2 API 詳細テスト")
print("=" * 50)

# 1. ヘルスチェック
print("\n1. ヘルスチェック...")
try:
    response = requests.get(f"{BASE_URL}/api/v2/health/")
    print(f"   ステータスコード: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   システム状態: {data['status']}")
        print(f"   サービス状態:")
        for service, info in data.get('services', {}).items():
            print(f"     - {service}: {info.get('status', 'unknown')}")
    else:
        print(f"   エラー: {response.text}")
except Exception as e:
    print(f"   例外エラー: {e}")
    sys.exit(1)

# 2. 認証テスト（新規ユーザー作成を含む）
print("\n2. 認証テスト...")
headers = {"Authorization": f"Bearer {TEST_EMAIL}"}
try:
    # まず、ユーザー情報を取得/作成
    response = requests.get(
        f"{BASE_URL}/api/v2/points/status",
        headers=headers
    )
    print(f"   ステータスコード: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ ポイント取得成功:")
        print(f"      現在のポイント: {data.get('current_points', 0)}")
        print(f"      累計獲得: {data.get('total_earned', 0)}")
        print(f"      累計使用: {data.get('total_spent', 0)}")
        print(f"      チャット作成可能: {data.get('can_create_chat', False)}")
    else:
        print(f"   ❌ エラー: {response.text}")
        
        # エラーの詳細を分析
        try:
            error_data = response.json()
            print(f"   エラー詳細: {error_data.get('detail', 'Unknown error')}")
        except:
            pass
            
except Exception as e:
    print(f"   例外エラー: {e}")

# 3. ポイント付与テスト（管理者権限が必要な場合はスキップ）
print("\n3. ポイント付与テスト...")
try:
    grant_data = {
        "transaction_type": "test_grant",
        "amount": 10,
        "description": "テストポイント付与"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v2/points/grant",
        headers=headers,
        json=grant_data
    )
    print(f"   ステータスコード: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ ポイント付与成功")
        print(f"      新しいポイント残高: {data.get('new_balance', 0)}")
    else:
        print(f"   ❌ エラー（権限不足の可能性）: {response.status_code}")
        
except Exception as e:
    print(f"   例外エラー: {e}")

# 4. チャット作成テスト
print("\n4. チャット作成テスト...")
try:
    chat_data = {
        "race_id": "test-race-v2-20250824",
        "race_date": "2025-08-24",
        "venue": "東京",
        "race_number": 11,
        "race_name": "V2テストレース",
        "horses": ["ドウデュース", "イクイノックス"],
        "jockeys": ["武豊", "C.ルメール"],
        "posts": [1, 2],
        "horse_numbers": [1, 2]
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v2/chat/create",
        headers=headers,
        json=chat_data
    )
    print(f"   ステータスコード: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        chat_id = data.get('chat_id')
        print(f"   ✅ チャット作成成功")
        print(f"      チャットID: {chat_id}")
        print(f"      レース名: {data.get('race_name')}")
        print(f"      出走頭数: {data.get('horse_count')}")
        
        # 5. メッセージ送信テスト
        if chat_id:
            print("\n5. メッセージ送信テスト...")
            message_data = {
                "message": "このレースをIMLogicで分析してください",
                "ai_type": "imlogic"
            }
            
            response = requests.post(
                f"{BASE_URL}/api/v2/chat/session/{chat_id}/message",
                headers=headers,
                json=message_data
            )
            print(f"   ステータスコード: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ メッセージ送信成功")
                if 'message' in data and 'content' in data['message']:
                    print(f"   AI応答（最初の100文字）:")
                    print(f"   {data['message']['content'][:100]}...")
            else:
                print(f"   ❌ エラー: {response.text}")
    else:
        print(f"   ❌ チャット作成エラー: {response.text}")
        
except Exception as e:
    print(f"   例外エラー: {e}")

print("\n" + "=" * 50)
print("テスト完了")