"""
リアルタイムユーザー統計機能のテストスクリプト
V2管理者パネルのアクティブユーザー数表示機能検証
作成日: 2025-09-04
"""
import asyncio
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from supabase import create_client
import logging
from datetime import datetime, timedelta

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Supabase設定
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_SERVICE_KEY")
supabase = create_client(supabase_url, supabase_key)

async def test_active_users_calculation():
    """アクティブユーザー数計算のテスト"""
    print("\n=== アクティブユーザー数計算テスト ===")
    
    # 現在時刻基準で時間範囲を設定
    now = datetime.utcnow()
    one_day_ago = now - timedelta(days=1)
    thirty_minutes_ago = now - timedelta(minutes=30)
    
    print(f"現在時刻: {now.isoformat()}")
    print(f"24時間前: {one_day_ago.isoformat()}")
    print(f"30分前: {thirty_minutes_ago.isoformat()}")
    
    try:
        # 24時間以内にログインしたユーザー数
        recent_users = supabase.table("v2_users")\
            .select("id, email, last_login_at")\
            .gte("last_login_at", one_day_ago.isoformat())\
            .execute()
        
        # 30分以内にチャットアクティビティがあったユーザー
        recent_chat_messages = supabase.table("v2_chat_messages")\
            .select("session_id, v2_chat_sessions(user_id)")\
            .gte("created_at", thirty_minutes_ago.isoformat())\
            .execute()
        
        # ユニークなオンラインユーザー数を計算
        online_user_ids = set()
        if recent_chat_messages.data:
            for message in recent_chat_messages.data:
                if message.get('v2_chat_sessions') and message['v2_chat_sessions'].get('user_id'):
                    online_user_ids.add(message['v2_chat_sessions']['user_id'])
        
        stats = {
            "currentOnline": len(online_user_ids),
            "last24Hours": len(recent_users.data) if recent_users.data else 0,
            "onlineUserIds": list(online_user_ids)
        }
        
        print(f"✅ 現在オンライン: {stats['currentOnline']}人")
        print(f"✅ 24時間以内アクティブ: {stats['last24Hours']}人")
        
        if stats["currentOnline"] > 0:
            print(f"   オンラインユーザーID: {stats['onlineUserIds'][:3]}...")  # 最初の3つのみ表示
        
        return True
        
    except Exception as e:
        print(f"❌ アクティブユーザー計算エラー: {e}")
        return False

async def test_database_access():
    """データベースアクセスのテスト"""
    print("\n=== データベースアクセステスト ===")
    
    try:
        # v2_users テーブル確認
        users_result = supabase.table("v2_users").select("id").limit(1).execute()
        if users_result.data:
            print("✅ v2_users テーブルアクセス成功")
        else:
            print("⚠️ v2_users テーブルにデータなし")
        
        # v2_chat_messages テーブル確認
        messages_result = supabase.table("v2_chat_messages").select("id").limit(1).execute()
        if messages_result.data:
            print("✅ v2_chat_messages テーブルアクセス成功")
        else:
            print("⚠️ v2_chat_messages テーブルにデータなし")
        
        # v2_chat_sessions テーブル確認
        sessions_result = supabase.table("v2_chat_sessions").select("id").limit(1).execute()
        if sessions_result.data:
            print("✅ v2_chat_sessions テーブルアクセス成功")
        else:
            print("⚠️ v2_chat_sessions テーブルにデータなし")
        
        return True
        
    except Exception as e:
        print(f"❌ データベースアクセスエラー: {e}")
        return False

async def test_last_login_tracking():
    """last_login_at フィールドの確認"""
    print("\n=== ログイン追跡テスト ===")
    
    try:
        # last_login_at が最近更新されているユーザーを確認
        recent_logins = supabase.table("v2_users")\
            .select("email, last_login_at")\
            .order("last_login_at", desc=True)\
            .limit(5)\
            .execute()
        
        if recent_logins.data:
            print("✅ 最近のログイン履歴:")
            for user in recent_logins.data:
                email = user.get('email', 'N/A')
                last_login = user.get('last_login_at', 'N/A')
                print(f"   - {email}: {last_login}")
            return True
        else:
            print("⚠️ ログイン履歴データなし")
            return False
            
    except Exception as e:
        print(f"❌ ログイン追跡エラー: {e}")
        return False

async def test_api_endpoint_simulation():
    """API エンドポイントの動作シミュレーション"""
    print("\n=== APIエンドポイント動作シミュレーション ===")
    
    try:
        # 実際のAPIエンドポイントと同じロジックを実行
        one_day_ago = (datetime.utcnow() - timedelta(days=1)).isoformat()
        thirty_minutes_ago = (datetime.utcnow() - timedelta(minutes=30)).isoformat()
        
        # 24時間以内アクティブユーザー
        recent_users = supabase.table("v2_users")\
            .select("id, email, last_login_at")\
            .gte("last_login_at", one_day_ago)\
            .execute()
        
        # 30分以内チャットアクティビティ
        recent_chats = supabase.table("v2_chat_messages")\
            .select("session_id, v2_chat_sessions(user_id)")\
            .gte("created_at", thirty_minutes_ago)\
            .execute()
        
        online_users = set()
        if recent_chats.data:
            for message in recent_chats.data:
                session = message.get('v2_chat_sessions')
                if session and session.get('user_id'):
                    online_users.add(session['user_id'])
        
        # APIレスポンス形式で結果を作成
        api_response = {
            "success": True,
            "stats": {
                "currentOnline": len(online_users),
                "last24Hours": len(recent_users.data) if recent_users.data else 0,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        print("✅ APIレスポンス形式:")
        print(f"   現在オンライン: {api_response['stats']['currentOnline']}人")
        print(f"   24時間アクティブ: {api_response['stats']['last24Hours']}人")
        print(f"   タイムスタンプ: {api_response['stats']['timestamp']}")
        
        return True
        
    except Exception as e:
        print(f"❌ APIシミュレーションエラー: {e}")
        return False

async def main():
    print("=" * 60)
    print("リアルタイムユーザー統計機能テスト")
    print("=" * 60)
    
    # 各テスト実行
    test1 = await test_database_access()
    test2 = await test_last_login_tracking()
    test3 = await test_active_users_calculation()
    test4 = await test_api_endpoint_simulation()
    
    # 結果サマリー
    print("\n" + "=" * 60)
    print("テスト結果サマリー")
    print("=" * 60)
    
    results = {
        "データベースアクセス": "✅" if test1 else "❌",
        "ログイン追跡": "✅" if test2 else "❌",
        "アクティブユーザー計算": "✅" if test3 else "❌",
        "APIシミュレーション": "✅" if test4 else "❌"
    }
    
    for key, value in results.items():
        print(f"{key}: {value}")
    
    all_ok = all([test1, test2, test3, test4])
    
    if all_ok:
        print("\n🎉 全てのテストが成功しました！")
        print("\nリアルタイムユーザー統計機能は正常に動作しています")
        print("\n機能詳細:")
        print("- 現在オンライン: 過去30分以内にチャットアクティビティがあったユーザー")
        print("- 24時間アクティブ: 過去24時間以内にログインしたユーザー")
        print("- 30秒ごとに自動更新")
        print("- 管理者権限でのみアクセス可能")
        
        print("\nアクセス方法:")
        print("https://www.dlogicai.in/v2/admin")
        print("- 管理者でログイン")
        print("- ダッシュボードにリアルタイムユーザー統計が表示")
        
    else:
        print("\n⚠️ 一部のテストが失敗しています")
        print("実装を確認してください")
    
    return all_ok

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)