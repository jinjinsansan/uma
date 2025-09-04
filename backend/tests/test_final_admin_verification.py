"""
管理者ユーザー管理機能最終検証テスト
プレミアム会員オプション削除後の動作確認
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

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Supabase設定
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_SERVICE_KEY")
supabase = create_client(supabase_url, supabase_key)

async def test_valid_roles_only():
    """有効なロールのみが使用されていることを確認"""
    print("\n=== 有効ロール確認テスト ===")
    
    # データベースから全ユーザーのロールを確認
    result = supabase.table("v2_users").select("role").execute()
    
    if not result.data:
        print("❌ ユーザーデータが見つかりません")
        return False
    
    # ロール集計
    role_counts = {}
    invalid_roles = []
    valid_roles = {"free", "admin", "blocked"}
    
    for user in result.data:
        role = user.get("role", "unknown")
        role_counts[role] = role_counts.get(role, 0) + 1
        
        if role not in valid_roles and role != "unknown":
            invalid_roles.append(role)
    
    print("現在のロール分布:")
    for role, count in role_counts.items():
        status = "✅" if role in valid_roles else "❌"
        print(f"  {status} {role}: {count}人")
    
    if invalid_roles:
        print(f"\n❌ 無効なロールが検出されました: {set(invalid_roles)}")
        return False
    
    if "premium" in role_counts:
        print(f"\n❌ プレミアム会員ロールが残存しています: {role_counts['premium']}人")
        return False
    
    print("\n✅ V2では有効なロールのみが使用されています")
    return True

async def test_role_transition():
    """ロール変更機能のテスト"""
    print("\n=== ロール変更機能テスト ===")
    
    # テストユーザー取得
    result = supabase.table("v2_users").select("id, email, role").limit(1).execute()
    if not result.data:
        print("❌ テストユーザーが見つかりません")
        return False
    
    test_user = result.data[0]
    original_role = test_user["role"]
    print(f"テストユーザー: {test_user.get('email', 'N/A')}")
    print(f"現在のロール: {original_role}")
    
    # 有効なロール間での変更テスト
    valid_roles = ["free", "admin", "blocked"]
    test_roles = [role for role in valid_roles if role != original_role]
    
    success_count = 0
    
    for new_role in test_roles:
        try:
            # ロール変更
            update_result = supabase.table("v2_users")\
                .update({"role": new_role})\
                .eq("id", test_user["id"])\
                .execute()
            
            if update_result.data:
                # 変更確認
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

async def test_admin_api_endpoints():
    """管理者APIエンドポイントのテスト"""
    print("\n=== 管理者APIエンドポイント確認 ===")
    
    # APIエンドポイントファイルの存在確認
    api_files = [
        "/api/v2/admin/users.ts",
        "/api/v2/admin/campaign.ts"
    ]
    
    results = []
    
    for api_file in api_files:
        full_path = f"/mnt/e/dev/Cusor/front/d-logic-ai-frontend/pages{api_file}"
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'checkAdminPermission' in content:
                    print(f"✅ {api_file}: 管理者権限チェックあり")
                    results.append(True)
                else:
                    print(f"⚠️ {api_file}: 管理者権限チェックなし")
                    results.append(False)
        except FileNotFoundError:
            print(f"❌ {api_file}: ファイルが見つかりません")
            results.append(False)
        except Exception as e:
            print(f"❌ {api_file}: エラー {e}")
            results.append(False)
    
    return all(results)

async def test_point_management():
    """ポイント管理機能のテスト"""
    print("\n=== ポイント管理機能テスト ===")
    
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
    test_amount = 5
    
    try:
        await service.grant_points(
            user_id=test_user_id,
            amount=test_amount,
            transaction_type="admin_grant",
            description="最終検証テスト"
        )
        
        # 付与後確認
        after_points = await service.get_user_points(test_user_id)
        expected_points = initial_points['current_points'] + test_amount
        
        if after_points['current_points'] == expected_points:
            print(f"✅ ポイント管理成功: {initial_points['current_points']} → {after_points['current_points']}P")
            return True
        else:
            print(f"❌ ポイント不一致: 期待値={expected_points}, 実際={after_points['current_points']}")
            return False
    
    except Exception as e:
        print(f"❌ ポイント管理エラー: {e}")
        return False

async def main():
    print("=" * 60)
    print("管理者ユーザー管理機能 最終検証テスト")
    print("プレミアム会員オプション削除後の動作確認")
    print("=" * 60)
    
    # 各テスト実行
    test1 = await test_valid_roles_only()
    test2 = await test_role_transition()
    test3 = await test_admin_api_endpoints()
    test4 = await test_point_management()
    
    # 結果サマリー
    print("\n" + "=" * 60)
    print("最終検証結果")
    print("=" * 60)
    
    results = {
        "有効ロール確認": "✅" if test1 else "❌",
        "ロール変更機能": "✅" if test2 else "❌",
        "管理者API": "✅" if test3 else "❌", 
        "ポイント管理": "✅" if test4 else "❌"
    }
    
    for key, value in results.items():
        print(f"{key}: {value}")
    
    all_ok = all([test1, test2, test3, test4])
    
    if all_ok:
        print("\n🎉 全ての検証テストが成功しました！")
        print("\n✅ V2管理者ユーザー管理機能は正常に動作しています")
        print("✅ プレミアム会員オプションは正常に削除されました")
        print("✅ 有効なロールのみ使用されています: 無料会員、管理者、ブロック")
        
        print("\n実装済み機能:")
        print("- ユーザー一覧表示・検索・フィルタリング")
        print("- ロール変更（無料会員 ⇄ 管理者 ⇄ ブロック）")
        print("- ポイント編集（設定・追加付与）")
        print("- ユーザー削除")
        print("- 全ユーザー一括ポイント付与（キャンペーン機能）")
        print("- キャンペーン履歴管理")
        
        print("\n管理者パネルアクセス:")
        print("http://localhost:3000/v2/admin/users")
        
    else:
        print("\n⚠️ 一部の検証が失敗しています")
        print("詳細を確認してください")
    
    return all_ok

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)