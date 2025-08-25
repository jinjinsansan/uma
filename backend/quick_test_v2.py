"""
V2 API クイックテスト（最小限のテスト）
"""
import requests
import json

# テスト設定
BASE_URL = "http://localhost:8000"  # ローカルで起動している場合
# BASE_URL = "https://uma-i30n.onrender.com"  # 本番環境
TEST_EMAIL = "test@example.com"

print("V2 API クイックテスト")
print("=" * 50)

# 1. ヘルスチェック
print("\n1. ヘルスチェック...")
try:
    response = requests.get(f"{BASE_URL}/api/v2/health/")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ ヘルスチェック成功: {data['status']}")
        for service, status in data.get('services', {}).items():
            print(f"   - {service}: {status.get('status', 'unknown')}")
    else:
        print(f"❌ ヘルスチェック失敗: {response.status_code}")
        print(f"   レスポンス: {response.text}")
except Exception as e:
    print(f"❌ ヘルスチェックエラー: {e}")

# 2. ポイント状態（認証テスト）
print("\n2. ポイント状態取得...")
headers = {"Authorization": f"Bearer {TEST_EMAIL}"}
try:
    response = requests.get(f"{BASE_URL}/api/v2/points/status", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ ポイント状態取得成功:")
        print(f"   - 現在のポイント: {data.get('current_points', 0)}")
        print(f"   - チャット作成可能: {data.get('can_create_chat', False)}")
    else:
        print(f"❌ ポイント状態取得失敗: {response.status_code}")
        print(f"   レスポンス: {response.text}")
except Exception as e:
    print(f"❌ ポイント状態取得エラー: {e}")

print("\n" + "=" * 50)
print("テスト完了")
print("\n注意: 完全なテストを実行するには:")
print("- ローカルでバックエンドを起動: cd backend && uvicorn main:app --reload")
print("- または本番環境URLに変更してください")