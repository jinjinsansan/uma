"""
楽観的ロック機能のテストスクリプト
同時実行時の競合検出と自動リトライを確認
"""
import asyncio
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from services.v2.points_service import V2PointsService, InsufficientPointsError, ConcurrencyError
from supabase import create_client
import logging

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Supabase設定
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_SERVICE_KEY")
supabase = create_client(supabase_url, supabase_key)

async def test_single_use():
    """単一のポイント使用テスト"""
    print("\n=== 単一ポイント使用テスト ===")
    
    service = V2PointsService()
    
    # テストユーザー取得
    result = supabase.table("v2_users").select("id").limit(1).execute()
    if not result.data:
        print("❌ テストユーザーが見つかりません")
        return False
    
    test_user_id = result.data[0]["id"]
    
    # 現在のポイント確認
    points = await service.get_user_points(test_user_id)
    print(f"現在のポイント: {points['current_points']}")
    
    if points['current_points'] < 1:
        # ポイント付与
        print("ポイント不足のため、テスト用に10ポイント付与")
        await service.grant_points(
            user_id=test_user_id,
            amount=10,
            transaction_type="test_grant",
            description="楽観的ロックテスト用"
        )
        points = await service.get_user_points(test_user_id)
        print(f"付与後のポイント: {points['current_points']}")
    
    # ポイント使用テスト
    try:
        result = await service.use_points(
            user_id=test_user_id,
            amount=1,
            transaction_type="test_use",
            description="単一使用テスト"
        )
        print(f"✅ ポイント使用成功: 残高 {result['balance_after']}")
        return True
    except Exception as e:
        print(f"❌ ポイント使用失敗: {e}")
        return False

async def test_concurrent_use():
    """同時実行時の楽観的ロックテスト"""
    print("\n=== 同時実行楽観的ロックテスト ===")
    
    service = V2PointsService()
    
    # テストユーザー取得
    result = supabase.table("v2_users").select("id").limit(1).execute()
    if not result.data:
        print("❌ テストユーザーが見つかりません")
        return False
    
    test_user_id = result.data[0]["id"]
    
    # 十分なポイントを確保
    points = await service.get_user_points(test_user_id)
    if points['current_points'] < 10:
        await service.grant_points(
            user_id=test_user_id,
            amount=20,
            transaction_type="test_grant",
            description="同時実行テスト用"
        )
        points = await service.get_user_points(test_user_id)
    
    initial_points = points['current_points']
    print(f"初期ポイント: {initial_points}")
    
    # 同時に3つのポイント使用を実行
    async def use_points_task(task_id: int):
        try:
            result = await service.use_points(
                user_id=test_user_id,
                amount=1,
                transaction_type="concurrent_test",
                description=f"同時実行テスト #{task_id}"
            )
            print(f"  ✅ タスク{task_id}: 成功 (残高: {result['balance_after']})")
            return True
        except ConcurrencyError as e:
            print(f"  ⚠️  タスク{task_id}: 競合検出後リトライ中...")
            return False
        except Exception as e:
            print(f"  ❌ タスク{task_id}: エラー {e}")
            return False
    
    # 3つの非同期タスクを同時実行
    tasks = [use_points_task(i) for i in range(1, 4)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # 最終ポイント確認
    final_points = await service.get_user_points(test_user_id)
    used_points = initial_points - final_points['current_points']
    
    print(f"\n結果:")
    print(f"  初期ポイント: {initial_points}")
    print(f"  最終ポイント: {final_points['current_points']}")
    print(f"  使用ポイント: {used_points}")
    print(f"  期待使用ポイント: 3")
    
    success = used_points == 3
    if success:
        print("✅ 楽観的ロックが正常に動作しています")
    else:
        print("❌ ポイント不整合が発生しています")
    
    return success

async def test_insufficient_points():
    """ポイント不足時のテスト"""
    print("\n=== ポイント不足エラーテスト ===")
    
    service = V2PointsService()
    
    # テストユーザー取得
    result = supabase.table("v2_users").select("id").limit(1).execute()
    if not result.data:
        print("❌ テストユーザーが見つかりません")
        return False
    
    test_user_id = result.data[0]["id"]
    
    # 現在のポイント確認
    points = await service.get_user_points(test_user_id)
    current_points = points['current_points']
    
    # 現在のポイント + 100を要求
    try:
        await service.use_points(
            user_id=test_user_id,
            amount=current_points + 100,
            transaction_type="insufficient_test",
            description="ポイント不足テスト"
        )
        print("❌ ポイント不足エラーが発生しませんでした")
        return False
    except InsufficientPointsError as e:
        print(f"✅ 正しくポイント不足エラーが発生: {e}")
        return True
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        return False

async def main():
    print("=" * 50)
    print("楽観的ロック機能テスト")
    print("=" * 50)
    
    # 各テストを実行
    test1 = await test_single_use()
    test2 = await test_concurrent_use()
    test3 = await test_insufficient_points()
    
    # 結果サマリー
    print("\n" + "=" * 50)
    print("テスト結果サマリー")
    print("=" * 50)
    
    results = {
        "単一ポイント使用": "✅" if test1 else "❌",
        "同時実行制御": "✅" if test2 else "❌",
        "ポイント不足エラー": "✅" if test3 else "❌"
    }
    
    for key, value in results.items():
        print(f"{key}: {value}")
    
    all_ok = test1 and test2 and test3
    
    if all_ok:
        print("\n🎉 全てのテストが成功しました！")
        print("Phase 2の楽観的ロック実装は完了です。")
    else:
        print("\n⚠️  一部のテストが失敗しています。")
        print("実装を確認してください。")
    
    return all_ok

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)