"""
V2 API テストスクリプト
"""
import asyncio
import aiohttp
import json
from datetime import datetime

# テスト用の設定
BASE_URL = "http://localhost:8000"  # ローカルテスト用
# BASE_URL = "https://uma-i30n.onrender.com"  # 本番環境

# テスト用ユーザー
TEST_USER_EMAIL = "test@example.com"
TEST_USER_ID = "test-user-id"

# 色付きログ出力
def log_success(message):
    print(f"✅ {message}")

def log_error(message):
    print(f"❌ {message}")

def log_info(message):
    print(f"ℹ️  {message}")

def log_section(title):
    print(f"\n{'=' * 50}")
    print(f"📋 {title}")
    print(f"{'=' * 50}")


async def test_points_api():
    """ポイントAPIのテスト"""
    log_section("ポイントAPI テスト")
    
    async with aiohttp.ClientSession() as session:
        # 1. ポイント状態取得
        log_info("ポイント状態を取得...")
        headers = {"Authorization": f"Bearer {TEST_USER_EMAIL}"}
        
        try:
            async with session.get(
                f"{BASE_URL}/api/v2/points/status",
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    log_success(f"ポイント状態取得成功: {data}")
                    return data
                else:
                    error_text = await response.text()
                    log_error(f"ポイント状態取得失敗: {response.status} - {error_text}")
        except Exception as e:
            log_error(f"ポイント状態取得エラー: {e}")
            
        # 2. ポイント付与テスト
        log_info("ポイント付与テスト...")
        grant_data = {
            "transaction_type": "test_grant",
            "amount": 10,
            "description": "テストポイント付与"
        }
        
        try:
            async with session.post(
                f"{BASE_URL}/api/v2/points/grant",
                headers=headers,
                json=grant_data
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    log_success(f"ポイント付与成功: {data}")
                else:
                    error_text = await response.text()
                    log_error(f"ポイント付与失敗: {response.status} - {error_text}")
        except Exception as e:
            log_error(f"ポイント付与エラー: {e}")
            
        # 3. 取引履歴取得
        log_info("取引履歴を取得...")
        try:
            async with session.get(
                f"{BASE_URL}/api/v2/points/transactions",
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    log_success(f"取引履歴取得成功: {len(data['transactions'])}件")
                else:
                    error_text = await response.text()
                    log_error(f"取引履歴取得失敗: {response.status} - {error_text}")
        except Exception as e:
            log_error(f"取引履歴取得エラー: {e}")


async def test_chat_api():
    """チャットAPIのテスト"""
    log_section("チャットAPI テスト")
    
    async with aiohttp.ClientSession() as session:
        headers = {"Authorization": f"Bearer {TEST_USER_EMAIL}"}
        
        # 1. チャット作成
        log_info("チャットセッション作成...")
        create_data = {
            "race_id": "test-race-20250824",
            "race_date": "2025-08-24",
            "venue": "東京",
            "race_number": 11,
            "race_name": "テストレース",
            "horses": ["ドウデュース", "イクイノックス", "リバティアイランド"],
            "jockeys": ["武豊", "C.ルメール", "川田将雅"],
            "posts": [1, 2, 3],
            "horse_numbers": [1, 2, 3]
        }
        
        chat_id = None
        try:
            async with session.post(
                f"{BASE_URL}/api/v2/chat/create",
                headers=headers,
                json=create_data
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    chat_id = data["chat_id"]
                    log_success(f"チャット作成成功: ID={chat_id}")
                else:
                    error_text = await response.text()
                    log_error(f"チャット作成失敗: {response.status} - {error_text}")
        except Exception as e:
            log_error(f"チャット作成エラー: {e}")
            
        # 2. セッション一覧取得
        log_info("チャットセッション一覧取得...")
        try:
            async with session.get(
                f"{BASE_URL}/api/v2/chat/sessions",
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    log_success(f"セッション一覧取得成功: {len(data['sessions'])}件")
                else:
                    error_text = await response.text()
                    log_error(f"セッション一覧取得失敗: {response.status} - {error_text}")
        except Exception as e:
            log_error(f"セッション一覧取得エラー: {e}")
            
        # 3. 特定セッション取得
        if chat_id:
            log_info(f"セッション {chat_id} を取得...")
            try:
                async with session.get(
                    f"{BASE_URL}/api/v2/chat/session/{chat_id}",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        log_success(f"セッション取得成功: {data['race_name']}")
                    else:
                        error_text = await response.text()
                        log_error(f"セッション取得失敗: {response.status} - {error_text}")
            except Exception as e:
                log_error(f"セッション取得エラー: {e}")
                
        # 4. メッセージ送信
        if chat_id:
            log_info("IMLogicメッセージ送信...")
            message_data = {
                "message": "このレースを分析してください",
                "ai_type": "imlogic"
            }
            
            try:
                async with session.post(
                    f"{BASE_URL}/api/v2/chat/session/{chat_id}/message",
                    headers=headers,
                    json=message_data
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        log_success(f"メッセージ送信成功")
                        log_info(f"AI応答: {data['message']['content'][:100]}...")
                    else:
                        error_text = await response.text()
                        log_error(f"メッセージ送信失敗: {response.status} - {error_text}")
            except Exception as e:
                log_error(f"メッセージ送信エラー: {e}")


async def test_integration():
    """統合テスト"""
    log_section("統合テスト")
    
    # 1. ポイントAPI
    await test_points_api()
    
    # 2. チャットAPI
    await test_chat_api()
    
    log_section("テスト完了")


async def main():
    """メイン関数"""
    print(f"""
╔═══════════════════════════════════════════════════╗
║          V2 API テストスクリプト                   ║
║                                                   ║
║  対象: {BASE_URL:<40} ║
║  時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S'):<40} ║
╚═══════════════════════════════════════════════════╝
    """)
    
    await test_integration()


if __name__ == "__main__":
    asyncio.run(main())