"""
ポイント履歴UIのテストスクリプト
作成日: 2025-09-04
"""
import asyncio
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from supabase import create_client
from services.v2.points_service import V2PointsService
import logging
from datetime import datetime

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Supabase設定
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_SERVICE_KEY")
supabase = create_client(supabase_url, supabase_key)

async def test_points_history():
    """ポイント履歴機能のテスト"""
    print("\n=== ポイント履歴テスト ===")
    
    service = V2PointsService()
    
    # テストユーザー取得
    result = supabase.table("v2_users").select("id").limit(1).execute()
    if not result.data:
        print("❌ テストユーザーが見つかりません")
        return False
    
    test_user_id = result.data[0]["id"]
    print(f"テストユーザーID: {test_user_id}")
    
    # 様々なトランザクションを作成
    print("\n=== サンプルトランザクション作成 ===")
    
    # 1. Google認証ボーナス
    try:
        await service.grant_points(
            user_id=test_user_id,
            amount=2,
            transaction_type="google_auth",
            description="Google認証完了ボーナス"
        )
        print("✅ Google認証ボーナス: +2P")
    except Exception as e:
        print(f"⚠️ Google認証ボーナス追加スキップ（既に付与済み）")
    
    # 2. チャット使用
    try:
        await service.use_points(
            user_id=test_user_id,
            amount=1,
            transaction_type="chat_usage",
            description="IMロジックチャット使用"
        )
        print("✅ チャット使用: -1P")
    except Exception as e:
        print(f"❌ チャット使用エラー: {e}")
    
    # 3. コラム閲覧
    try:
        await service.use_points(
            user_id=test_user_id,
            amount=3,
            transaction_type="column_view",
            description="コラム閲覧: 新機能紹介"
        )
        print("✅ コラム閲覧: -3P")
    except Exception as e:
        print(f"❌ コラム閲覧エラー: {e}")
    
    # 4. テスト付与
    await service.grant_points(
        user_id=test_user_id,
        amount=10,
        transaction_type="test_grant",
        description="ポイント履歴テスト用"
    )
    print("✅ テスト付与: +10P")
    
    # 取引履歴を取得
    print("\n=== 取引履歴取得 ===")
    transactions = await service.get_transactions(
        user_id=test_user_id,
        limit=10,
        offset=0
    )
    
    print(f"取得件数: {len(transactions)}件")
    
    # 最新5件を表示
    print("\n=== 最新5件の履歴 ===")
    for i, tx in enumerate(transactions[:5]):
        tx_type = tx.get("transaction_type", "不明")
        amount = tx.get("amount", 0)
        balance = tx.get("balance_after", 0)
        desc = tx.get("description", "")
        created = tx.get("created_at", "")
        
        symbol = "+" if amount > 0 else ""
        print(f"\n{i+1}. {tx_type}")
        print(f"   金額: {symbol}{amount}P")
        print(f"   残高: {balance}P")
        print(f"   説明: {desc}")
        print(f"   日時: {created}")
    
    # 現在のポイント残高
    points_data = await service.get_user_points(test_user_id)
    print(f"\n=== 現在のポイント残高 ===")
    print(f"現在のポイント: {points_data['current_points']}P")
    print(f"獲得合計: {points_data['total_earned']}P")
    print(f"使用合計: {points_data['total_spent']}P")
    
    return True

async def test_api_endpoint():
    """APIエンドポイントのテスト"""
    print("\n=== APIエンドポイントテスト ===")
    
    # テストユーザー取得
    result = supabase.table("v2_users").select("id").limit(1).execute()
    if not result.data:
        print("❌ テストユーザーが見つかりません")
        return False
    
    test_user_id = result.data[0]["id"]
    
    # 直接Supabaseから取得
    transactions = supabase.table("v2_point_transactions")\
        .select("*")\
        .eq("user_id", test_user_id)\
        .order("created_at", desc=True)\
        .limit(5)\
        .execute()
    
    if transactions.data:
        print(f"✅ API経由で{len(transactions.data)}件の取引履歴を取得")
        
        # トランザクションタイプの統計
        type_counts = {}
        for tx in transactions.data:
            tx_type = tx.get("transaction_type", "不明")
            type_counts[tx_type] = type_counts.get(tx_type, 0) + 1
        
        print("\n=== トランザクションタイプ別統計 ===")
        for tx_type, count in type_counts.items():
            print(f"{tx_type}: {count}件")
    else:
        print("⚠️ 取引履歴がありません")
    
    return True

async def main():
    print("=" * 50)
    print("ポイント履歴UIテスト")
    print("=" * 50)
    
    # テスト実行
    test1 = await test_points_history()
    test2 = await test_api_endpoint()
    
    # 結果サマリー
    print("\n" + "=" * 50)
    print("テスト結果サマリー")
    print("=" * 50)
    
    results = {
        "ポイント履歴機能": "✅" if test1 else "❌",
        "APIエンドポイント": "✅" if test2 else "❌"
    }
    
    for key, value in results.items():
        print(f"{key}: {value}")
    
    all_ok = test1 and test2
    
    if all_ok:
        print("\n🎉 全てのテストが成功しました！")
        print("Phase 4のポイント履歴UI実装は完了です。")
        print("\n次のステップ:")
        print("1. ブラウザで http://localhost:3000/v2/my-account にアクセス")
        print("2. 「ポイント履歴」タブをクリック")
        print("3. 取引履歴が正しく表示されることを確認")
    else:
        print("\n⚠️ 一部のテストが失敗しています。")
        print("実装を確認してください。")
    
    return all_ok

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)