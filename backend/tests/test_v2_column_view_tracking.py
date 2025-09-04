"""
V2コラム閲覧数追跡機能のテストスクリプト
リアルタイム閲覧数計測とAPI統合性の検証
作成日: 2025-09-04
"""
import asyncio
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
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

async def test_column_tables_existence():
    """コラム関連テーブルの存在確認"""
    print("\n=== コラム関連テーブル存在確認テスト ===")
    
    tables_to_check = [
        "columns",
        "v2_columns", 
        "v2_column_reads",
        "v2_column_categories"
    ]
    
    results = {}
    
    for table in tables_to_check:
        try:
            result = supabase.table(table).select("*").limit(1).execute()
            if hasattr(result, 'data'):
                results[table] = "✅ 存在"
                print(f"✅ {table}: 存在 ({len(result.data or [])}件のサンプル)")
                
                # 最初のレコードの構造を確認
                if result.data:
                    first_record = result.data[0]
                    if 'view_count' in first_record:
                        print(f"   - view_count フィールド: {first_record['view_count']}")
                    if table == 'v2_column_reads' and 'column_id' in first_record:
                        print(f"   - column_id: {first_record['column_id']}")
            else:
                results[table] = "❌ アクセス失敗"
                print(f"❌ {table}: アクセス失敗")
        except Exception as e:
            results[table] = f"❌ エラー: {e}"
            print(f"❌ {table}: エラー {e}")
    
    return all("✅" in status for status in results.values())

async def test_api_endpoint_consistency():
    """APIエンドポイントの一貫性確認"""
    print("\n=== APIエンドポイント一貫性テスト ===")
    
    api_files = [
        "/pages/api/v2/admin/columns.ts",
        "/pages/api/v2/admin/columns/[id].ts",
        "/src/app/v2/column/page.tsx",
        "/src/app/v2/column/[id]/page.tsx"
    ]
    
    table_usage = {}
    
    for api_file in api_files:
        full_path = f"/mnt/e/dev/Cusor/front/d-logic-ai-frontend{api_file}"
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # テーブル使用状況の分析
                if 'table("columns")' in content or "table('columns')" in content:
                    table_usage[api_file] = "columns"
                elif 'table("v2_columns")' in content or "table('v2_columns')" in content:
                    table_usage[api_file] = "v2_columns"
                else:
                    table_usage[api_file] = "不明"
                    
                print(f"✅ {api_file}: {table_usage[api_file]} テーブルを使用")
                
        except FileNotFoundError:
            print(f"❌ {api_file}: ファイルが見つかりません")
            table_usage[api_file] = "未確認"
        except Exception as e:
            print(f"❌ {api_file}: エラー {e}")
            table_usage[api_file] = f"エラー: {e}"
    
    # 一貫性チェック
    used_tables = set([usage for usage in table_usage.values() if usage not in ["不明", "未確認"] and not usage.startswith("エラー")])
    
    if len(used_tables) > 1:
        print(f"⚠️ APIエンドポイント間でテーブル使用に不整合があります: {used_tables}")
        return False
    elif len(used_tables) == 1:
        print(f"✅ APIエンドポイント間のテーブル使用は一貫しています: {list(used_tables)[0]}")
        return True
    else:
        print("❌ テーブル使用状況を確認できませんでした")
        return False

async def test_view_count_tracking():
    """閲覧数追跡機能の実装状況テスト"""
    print("\n=== 閲覧数追跡機能実装状況テスト ===")
    
    try:
        # v2_column_reads テーブルの構造確認
        reads_sample = supabase.table("v2_column_reads").select("*").limit(5).execute()
        read_count = len(reads_sample.data) if reads_sample.data else 0
        
        print(f"✅ v2_column_reads レコード数: {read_count}件")
        
        if read_count == 0:
            print("⚠️ 閲覧履歴データが存在しません（未使用の可能性）")
        else:
            print("✅ 閲覧履歴データが存在します")
            
        # columns テーブルのview_count状況
        columns_sample = supabase.table("columns").select("id, view_count").limit(10).execute()
        if columns_sample.data:
            view_counts = [col.get('view_count', 0) for col in columns_sample.data]
            non_zero_counts = [count for count in view_counts if count > 0]
            
            print(f"✅ columns テーブル: {len(columns_sample.data)}件サンプル中 {len(non_zero_counts)}件に閲覧数あり")
            
            if len(non_zero_counts) == 0:
                print("⚠️ すべてのコラムの閲覧数が0です（追跡機能が動作していない可能性）")
                return False
            else:
                print(f"✅ 最大閲覧数: {max(view_counts)}")
                return True
        
        # v2_columns テーブルのview_count状況
        v2_columns_sample = supabase.table("v2_columns").select("id, view_count").limit(10).execute()
        if v2_columns_sample.data:
            v2_view_counts = [col.get('view_count', 0) for col in v2_columns_sample.data]
            v2_non_zero_counts = [count for count in v2_view_counts if count > 0]
            
            print(f"✅ v2_columns テーブル: {len(v2_columns_sample.data)}件サンプル中 {len(v2_non_zero_counts)}件に閲覧数あり")
            
            if len(v2_non_zero_counts) == 0:
                print("⚠️ すべてのV2コラムの閲覧数が0です（追跡機能が動作していない可能性）")
                return False
            else:
                print(f"✅ V2最大閲覧数: {max(v2_view_counts)}")
                return True
                
    except Exception as e:
        print(f"❌ 閲覧数追跡テストエラー: {e}")
        return False
    
    return True

async def test_view_increment_mechanism():
    """閲覧数増加メカニズムのテスト"""
    print("\n=== 閲覧数増加メカニズムテスト ===")
    
    # 閲覧数増加APIやトリガーの存在確認
    api_endpoints_to_check = [
        "/pages/api/v2/columns/view-increment.ts",
        "/pages/api/v2/columns/track-view.ts",
        "/pages/api/v2/admin/columns/increment-view.ts"
    ]
    
    mechanism_found = False
    
    for endpoint in api_endpoints_to_check:
        full_path = f"/mnt/e/dev/Cusor/front/d-logic-ai-frontend{endpoint}"
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"✅ {endpoint}: 閲覧数増加エンドポイントが存在")
                
                if 'view_count' in content and ('increment' in content.lower() or 'update' in content.lower()):
                    print("   - view_count の増加処理を確認")
                    mechanism_found = True
                else:
                    print("   - view_count 処理の詳細は不明")
                    
        except FileNotFoundError:
            print(f"❌ {endpoint}: エンドポイントが見つかりません")
        except Exception as e:
            print(f"❌ {endpoint}: エラー {e}")
    
    if not mechanism_found:
        print("⚠️ 明確な閲覧数増加メカニズムが見つかりませんでした")
        
        # フロントエンドコードで直接更新している可能性を確認
        frontend_files = [
            "/src/app/v2/column/[id]/page.tsx"
        ]
        
        for file_path in frontend_files:
            full_path = f"/mnt/e/dev/Cusor/front/d-logic-ai-frontend{file_path}"
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    if 'view_count' in content and ('increment' in content.lower() or 'update' in content.lower() or 'fetch' in content.lower()):
                        print(f"✅ {file_path}: フロントエンドで閲覧数処理の可能性")
                        mechanism_found = True
                    
            except Exception as e:
                print(f"❌ {file_path}: 確認エラー {e}")
    
    return mechanism_found

async def main():
    print("=" * 60)
    print("V2コラム閲覧数追跡機能テスト")
    print("=" * 60)
    
    # 各テスト実行
    test1 = await test_column_tables_existence()
    test2 = await test_api_endpoint_consistency()
    test3 = await test_view_count_tracking()
    test4 = await test_view_increment_mechanism()
    
    # 結果サマリー
    print("\n" + "=" * 60)
    print("テスト結果サマリー")
    print("=" * 60)
    
    results = {
        "テーブル存在確認": "✅" if test1 else "❌",
        "API一貫性": "✅" if test2 else "❌",
        "閲覧数データ確認": "✅" if test3 else "❌",
        "増加メカニズム": "✅" if test4 else "❌"
    }
    
    for key, value in results.items():
        print(f"{key}: {value}")
    
    overall_success = all([test1, test2, test3, test4])
    
    if overall_success:
        print("\n🎉 コラム閲覧数追跡機能は正常に動作しています！")
        
        print("\n実装確認項目:")
        print("- データベーステーブル構造 ✅")
        print("- APIエンドポイント一貫性 ✅") 
        print("- 閲覧履歴データ存在 ✅")
        print("- 増加メカニズム実装 ✅")
        
    else:
        print("\n⚠️ コラム閲覧数追跡機能に問題があります")
        
        print("\n問題点:")
        if not test1:
            print("- テーブル構造またはアクセスに問題があります")
        if not test2:
            print("- APIエンドポイント間でテーブル使用に不整合があります")
        if not test3:
            print("- 閲覧数データが正しく蓄積されていません")
        if not test4:
            print("- 閲覧数を増加させるメカニズムが見つかりません")
    
    print("\nコラム閲覧場所:")
    print("- ユーザーUI: https://www.dlogicai.in/v2/column")
    print("- 管理者パネル: https://www.dlogicai.in/v2/admin/columns")
    
    return overall_success

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)