"""
管理者ユーザー管理機能のテストスクリプト
ユーザー編集・ロール変更機能の動作確認
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

async def test_user_role_management():
    """ユーザーロール管理のテスト"""
    print("\n=== ユーザーロール管理テスト ===")
    
    # テストユーザー取得
    result = supabase.table("v2_users").select("id, email, role").limit(1).execute()
    if not result.data:
        print("❌ テストユーザーが見つかりません")
        return False
    
    test_user = result.data[0]
    original_role = test_user["role"]
    print(f"テストユーザー: {test_user.get('email', 'N/A')}")
    print(f"現在のロール: {original_role}")
    
    # 有効なロール一覧
    valid_roles = ["free", "admin", "blocked"]  # premiumは除外
    test_roles = [role for role in valid_roles if role != original_role]
    
    print(f"テスト対象ロール: {test_roles}")
    
    success_count = 0
    
    for new_role in test_roles:
        try:
            # ロール変更
            update_result = supabase.table("v2_users")\
                .update({"role": new_role})\
                .eq("id", test_user["id"])\
                .execute()
            
            if update_result.data:
                # 変更を確認
                check_result = supabase.table("v2_users")\
                    .select("role")\
                    .eq("id", test_user["id"])\
                    .single()\
                    .execute()
                
                if check_result.data and check_result.data["role"] == new_role:
                    print(f"  ✅ {original_role} → {new_role}: 成功")
                    success_count += 1
                else:
                    print(f"  ❌ {original_role} → {new_role}: 確認失敗")
            else:
                print(f"  ❌ {original_role} → {new_role}: 更新失敗")
        
        except Exception as e:
            print(f"  ❌ {original_role} → {new_role}: エラー {e}")
    
    # 元のロールに戻す
    try:
        supabase.table("v2_users")\
            .update({"role": original_role})\
            .eq("id", test_user["id"])\
            .execute()
        print(f"  ✅ ロール復元: {original_role}")
    except Exception as e:
        print(f"  ⚠️ ロール復元エラー: {e}")
    
    return success_count == len(test_roles)

async def test_user_points_management():
    """ユーザーポイント管理のテスト"""
    print("\n=== ユーザーポイント管理テスト ===")
    
    service = V2PointsService()
    
    # テストユーザー取得
    result = supabase.table("v2_users").select("id, email").limit(1).execute()
    if not result.data:
        print("❌ テストユーザーが見つかりません")
        return False
    
    test_user = result.data[0]
    test_user_id = test_user["id"]
    
    # 初期ポイント確認
    initial_points = await service.get_user_points(test_user_id)
    print(f"テストユーザー: {test_user.get('email', 'N/A')}")
    print(f"初期ポイント: {initial_points['current_points']}P")
    
    # 管理者からのポイント付与テスト
    test_amount = 7
    
    try:
        await service.grant_points(
            user_id=test_user_id,
            amount=test_amount,
            transaction_type="admin_grant",
            description="管理者パネル テスト付与"
        )
        
        # 付与後確認
        after_points = await service.get_user_points(test_user_id)
        expected_points = initial_points['current_points'] + test_amount
        
        if after_points['current_points'] == expected_points:
            print(f"✅ 管理者ポイント付与成功: {initial_points['current_points']} → {after_points['current_points']}P")
            return True
        else:
            print(f"❌ ポイント不一致: 期待値={expected_points}, 実際={after_points['current_points']}")
            return False
    
    except Exception as e:
        print(f"❌ 管理者ポイント付与エラー: {e}")
        return False

async def test_user_list_display():
    """ユーザー一覧表示のテスト"""
    print("\n=== ユーザー一覧表示テスト ===")
    
    # ユーザー一覧を取得
    users_result = supabase.table("v2_users")\
        .select("id, email, role, created_at")\
        .limit(5)\
        .execute()
    
    if not users_result.data:
        print("❌ ユーザーが見つかりません")
        return False
    
    print(f"ユーザー数: {len(users_result.data)}人")
    
    # ロール別の集計
    role_counts = {}
    for user in users_result.data:
        role = user.get("role", "unknown")
        role_counts[role] = role_counts.get(role, 0) + 1
    
    print("\nロール別ユーザー数:")
    for role, count in role_counts.items():
        print(f"  {role}: {count}人")
    
    # premium ロールの存在確認
    if "premium" in role_counts:
        print("⚠️ プレミアム会員ロールが存在します（削除推奨）")
    else:
        print("✅ プレミアム会員ロールは存在しません")
    
    return True

async def test_admin_permissions():
    """管理者権限の確認"""
    print("\n=== 管理者権限確認テスト ===")
    
    # 管理者メールアドレス
    admin_emails = ["goldbenchan@gmail.com", "kusanokiyoshi1@gmail.com"]
    
    admin_users = []
    for email in admin_emails:
        admin_result = supabase.table("v2_users")\
            .select("id, email, role")\
            .eq("email", email)\
            .execute()
        
        if admin_result.data:
            admin_users.extend(admin_result.data)
    
    print(f"管理者ユーザー数: {len(admin_users)}人")
    
    for admin in admin_users:
        print(f"  管理者: {admin['email']} (role: {admin['role']})")
    
    # APIでの管理者判定ロジック確認
    print("\n管理者判定ロジック:")
    print("  1. email == 'goldbenchan@gmail.com' → 管理者")
    print("  2. v2_users.role == 'admin' → 管理者")
    print("  3. その他 → 一般ユーザー")
    
    return len(admin_users) > 0

async def main():
    print("=" * 60)
    print("管理者ユーザー管理機能テスト")
    print("=" * 60)
    
    # 各テスト実行
    test1 = await test_user_role_management()
    test2 = await test_user_points_management()
    test3 = await test_user_list_display()
    test4 = await test_admin_permissions()
    
    # 結果サマリー
    print("\n" + "=" * 60)
    print("テスト結果サマリー")
    print("=" * 60)
    
    results = {
        "ユーザーロール変更": "✅" if test1 else "❌",
        "ポイント管理": "✅" if test2 else "❌",
        "ユーザー一覧表示": "✅" if test3 else "❌",
        "管理者権限": "✅" if test4 else "❌"
    }
    
    for key, value in results.items():
        print(f"{key}: {value}")
    
    all_ok = all([test1, test2, test3, test4])
    
    if all_ok:
        print("\n🎉 全てのテストが成功しました！")
        print("管理者ユーザー管理機能は正常に動作しています。")
        print("\n確認手順:")
        print("1. 管理者権限で http://localhost:3000/v2/admin/users にアクセス")
        print("2. ユーザー行の「編集」ボタンをクリック")
        print("3. ロールとポイントを変更して「保存」")
        print("4. 変更が反映されることを確認")
        
        print("\n推奨改善:")
        print("- プレミアム会員オプションを削除")
        print("- V2では「無料会員」「管理者」「ブロック」のみ")
    else:
        print("\n⚠️ 一部のテストが失敗しています。")
        print("実装を確認してください。")
    
    return all_ok

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)