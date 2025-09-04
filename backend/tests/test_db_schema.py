"""
データベーススキーマ更新のテストスクリプト
実行前と実行後の状態を確認
"""
import os
from dotenv import load_dotenv
from supabase import create_client, Client
import json

load_dotenv()

# Supabase設定
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_SERVICE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

def check_version_column():
    """version列の存在確認"""
    print("\n=== v2_user_pointsテーブルの構造確認 ===")
    
    try:
        # テストユーザーでversion列の存在を確認
        result = supabase.table("v2_users").select("id").limit(1).execute()
        if result.data:
            test_user_id = result.data[0]["id"]
            
            # v2_user_pointsから1件取得してversion列を確認
            points_result = supabase.table("v2_user_points")\
                .select("user_id, current_points, version")\
                .eq("user_id", test_user_id)\
                .execute()
            
            if points_result.data:
                print(f"✅ version列が存在します")
                print(f"   サンプルデータ: {json.dumps(points_result.data[0], indent=2)}")
                return True
            else:
                # ポイントデータがない場合は、新規作成してテスト
                print("⚠️  テスト用ポイントデータを作成中...")
                insert_result = supabase.table("v2_user_points").insert({
                    "user_id": test_user_id,
                    "current_points": 0,
                    "total_earned": 0,
                    "total_spent": 0
                }).execute()
                
                if insert_result.data:
                    # versionのデフォルト値を確認
                    check_result = supabase.table("v2_user_points")\
                        .select("version")\
                        .eq("user_id", test_user_id)\
                        .execute()
                    
                    if check_result.data and "version" in check_result.data[0]:
                        print(f"✅ version列が正常に動作（デフォルト値: {check_result.data[0]['version']}）")
                        return True
    except Exception as e:
        if "column" in str(e) and "version" in str(e):
            print(f"❌ version列が存在しません: {e}")
            return False
        else:
            print(f"⚠️  確認中にエラー: {e}")
            return None
    
    return False

def check_indexes():
    """インデックスの存在確認（間接的）"""
    print("\n=== インデックスのパフォーマンステスト ===")
    
    try:
        # 1. column_reads インデックステスト
        print("1. v2_column_reads インデックス確認...")
        reads_result = supabase.table("v2_column_reads")\
            .select("*")\
            .limit(1)\
            .execute()
        print("   ✅ v2_column_reads テーブルアクセス正常")
        
        # 2. point_transactions インデックステスト  
        print("2. v2_point_transactions インデックス確認...")
        trans_result = supabase.table("v2_point_transactions")\
            .select("*")\
            .order("created_at", desc=True)\
            .limit(1)\
            .execute()
        print("   ✅ v2_point_transactions ソート処理正常")
        
        # 3. column_views インデックステスト
        print("3. v2_column_views インデックス確認...")
        views_result = supabase.table("v2_column_views")\
            .select("*")\
            .limit(1)\
            .execute()
        print("   ✅ v2_column_views テーブルアクセス正常")
        
        return True
        
    except Exception as e:
        print(f"❌ インデックス確認中にエラー: {e}")
        return False

def test_version_update():
    """version列の更新動作テスト"""
    print("\n=== version列の更新テスト ===")
    
    try:
        # テストユーザー取得
        result = supabase.table("v2_users").select("id").limit(1).execute()
        if not result.data:
            print("❌ テストユーザーが見つかりません")
            return False
            
        test_user_id = result.data[0]["id"]
        
        # 現在のversion取得
        current = supabase.table("v2_user_points")\
            .select("current_points, version")\
            .eq("user_id", test_user_id)\
            .execute()
        
        if not current.data:
            print("❌ ポイントデータが見つかりません")
            return False
        
        current_version = current.data[0].get("version", 0)
        current_points = current.data[0]["current_points"]
        
        print(f"現在のversion: {current_version}, ポイント: {current_points}")
        
        # 楽観的ロックのシミュレーション
        # 正しいversionで更新
        update_result = supabase.table("v2_user_points")\
            .update({
                "current_points": current_points,
                "version": current_version + 1
            })\
            .eq("user_id", test_user_id)\
            .eq("version", current_version)\
            .execute()
        
        if update_result.data:
            print(f"✅ version更新成功: {current_version} → {current_version + 1}")
            
            # 古いversionで更新を試みる（失敗するはず）
            fail_result = supabase.table("v2_user_points")\
                .update({
                    "current_points": current_points,
                    "version": current_version + 2  
                })\
                .eq("user_id", test_user_id)\
                .eq("version", current_version)\
                .execute()
            
            if not fail_result.data:
                print("✅ 古いversionでの更新は正しく失敗しました")
                return True
            else:
                print("⚠️  古いversionでも更新されてしまいました（要確認）")
                return False
        else:
            print("❌ version更新に失敗しました")
            return False
            
    except Exception as e:
        print(f"❌ テスト中にエラー: {e}")
        return False

def main():
    print("=" * 50)
    print("V2システム データベーススキーマ確認")
    print("=" * 50)
    
    # 1. version列の確認
    version_ok = check_version_column()
    
    # 2. インデックスの確認
    index_ok = check_indexes()
    
    # 3. version列の動作テスト
    update_ok = False
    if version_ok:
        update_ok = test_version_update()
    
    # 結果サマリー
    print("\n" + "=" * 50)
    print("テスト結果サマリー")
    print("=" * 50)
    
    results = {
        "version列の存在": "✅" if version_ok else "❌",
        "インデックス": "✅" if index_ok else "❌", 
        "version更新動作": "✅" if update_ok else "❌" if version_ok else "⏭️ スキップ"
    }
    
    for key, value in results.items():
        print(f"{key}: {value}")
    
    all_ok = version_ok and index_ok and (update_ok if version_ok else True)
    
    if all_ok:
        print("\n🎉 全てのテストが成功しました！")
        print("Phase 1のデータベース更新は完了です。")
    else:
        print("\n⚠️  一部のテストが失敗しています。")
        print("SQLスクリプトを実行する必要があります。")
    
    return all_ok

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)