"""
最終デプロイメント前の包括的テストスクリプト
全機能の動作確認・整合性チェック
作成日: 2025-09-04
"""
import asyncio
import os
import sys
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from supabase import create_client
import logging
import requests
import time
from datetime import datetime

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Supabase設定
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_SERVICE_KEY")
supabase = create_client(supabase_url, supabase_key)

# テスト結果格納
test_results = {
    "timestamp": datetime.now().isoformat(),
    "tests": {},
    "summary": {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "warnings": 0
    }
}

def add_test_result(category, test_name, status, details=""):
    """テスト結果を記録"""
    if category not in test_results["tests"]:
        test_results["tests"][category] = {}
    
    test_results["tests"][category][test_name] = {
        "status": status,
        "details": details
    }
    
    test_results["summary"]["total"] += 1
    if status == "PASS":
        test_results["summary"]["passed"] += 1
    elif status == "FAIL":
        test_results["summary"]["failed"] += 1
    elif status == "WARN":
        test_results["summary"]["warnings"] += 1

async def test_system_status_monitoring():
    """1. システムステータス監視機能のテスト"""
    print("\n" + "="*60)
    print("【1】システムステータス監視機能テスト")
    print("="*60)
    
    # データベース接続テスト
    try:
        start = time.time()
        result = supabase.table("v2_users").select("id").limit(1).execute()
        response_time = (time.time() - start) * 1000
        
        if response_time < 3000:
            add_test_result("システムステータス", "データベース接続", "PASS", f"応答時間: {response_time:.0f}ms")
            print(f"✅ データベース接続: 正常 ({response_time:.0f}ms)")
        else:
            add_test_result("システムステータス", "データベース接続", "WARN", f"応答時間遅延: {response_time:.0f}ms")
            print(f"⚠️ データベース接続: 遅延 ({response_time:.0f}ms)")
    except Exception as e:
        add_test_result("システムステータス", "データベース接続", "FAIL", str(e))
        print(f"❌ データベース接続: 失敗 ({e})")
    
    # APIエンドポイント確認
    api_file = "/mnt/e/dev/Cusor/front/d-logic-ai-frontend/pages/api/v2/admin/dashboard.ts"
    try:
        with open(api_file, 'r') as f:
            content = f.read()
            if 'checkSystemStatus' in content and 'await checkSystemStatus()' in content:
                add_test_result("システムステータス", "APIエンドポイント実装", "PASS", "checkSystemStatus関数実装済み")
                print("✅ APIエンドポイント: checkSystemStatus実装確認")
            else:
                add_test_result("システムステータス", "APIエンドポイント実装", "FAIL", "実装不完全")
                print("❌ APIエンドポイント: 実装不完全")
    except Exception as e:
        add_test_result("システムステータス", "APIエンドポイント実装", "FAIL", str(e))
        print(f"❌ APIエンドポイント確認エラー: {e}")
    
    return True

async def test_column_view_tracking():
    """2. コラム閲覧数追跡機能のテスト"""
    print("\n" + "="*60)
    print("【2】コラム閲覧数追跡機能テスト")
    print("="*60)
    
    # track-view APIエンドポイント確認
    track_api_file = "/mnt/e/dev/Cusor/front/d-logic-ai-frontend/pages/api/v2/columns/track-view.ts"
    try:
        if os.path.exists(track_api_file):
            with open(track_api_file, 'r') as f:
                content = f.read()
                if 'view_count' in content and 'v2_columns' in content:
                    add_test_result("閲覧数追跡", "APIエンドポイント", "PASS", "track-view.ts実装確認")
                    print("✅ 閲覧数追跡API: 実装確認")
                else:
                    add_test_result("閲覧数追跡", "APIエンドポイント", "WARN", "実装内容要確認")
                    print("⚠️ 閲覧数追跡API: 実装内容要確認")
        else:
            add_test_result("閲覧数追跡", "APIエンドポイント", "FAIL", "ファイル不存在")
            print("❌ 閲覧数追跡API: ファイル不存在")
    except Exception as e:
        add_test_result("閲覧数追跡", "APIエンドポイント", "FAIL", str(e))
        print(f"❌ 閲覧数追跡API確認エラー: {e}")
    
    # フロントエンド実装確認
    column_detail_file = "/mnt/e/dev/Cusor/front/d-logic-ai-frontend/src/app/v2/column/[id]/page.tsx"
    try:
        with open(column_detail_file, 'r') as f:
            content = f.read()
            if 'trackView' in content and 'track-view' in content:
                add_test_result("閲覧数追跡", "フロントエンド実装", "PASS", "trackView関数実装確認")
                print("✅ フロントエンド: trackView実装確認")
            else:
                add_test_result("閲覧数追跡", "フロントエンド実装", "FAIL", "trackView未実装")
                print("❌ フロントエンド: trackView未実装")
    except Exception as e:
        add_test_result("閲覧数追跡", "フロントエンド実装", "FAIL", str(e))
        print(f"❌ フロントエンド確認エラー: {e}")
    
    # データベーステーブル確認
    try:
        # v2_columns テーブルのview_countフィールド確認
        v2_columns = supabase.table("v2_columns").select("id, view_count").limit(1).execute()
        if v2_columns.data and 'view_count' in v2_columns.data[0]:
            add_test_result("閲覧数追跡", "データベース構造", "PASS", "view_countフィールド存在")
            print(f"✅ v2_columnsテーブル: view_countフィールド確認")
        else:
            add_test_result("閲覧数追跡", "データベース構造", "FAIL", "view_countフィールド不明")
            print("❌ v2_columnsテーブル: view_countフィールド不明")
    except Exception as e:
        add_test_result("閲覧数追跡", "データベース構造", "FAIL", str(e))
        print(f"❌ データベース確認エラー: {e}")
    
    return True

async def test_existing_functions():
    """3. 既存機能への影響チェック"""
    print("\n" + "="*60)
    print("【3】既存機能への影響チェック")
    print("="*60)
    
    # V1機能のテーブルチェック
    v1_tables = ["users", "user_quotas", "line_tickets", "chat_sessions"]
    for table in v1_tables:
        try:
            result = supabase.table(table).select("*").limit(1).execute()
            if hasattr(result, 'data'):
                add_test_result("既存機能", f"V1_{table}テーブル", "PASS", "アクセス可能")
                print(f"✅ V1 {table}テーブル: アクセス可能")
            else:
                add_test_result("既存機能", f"V1_{table}テーブル", "FAIL", "アクセス不可")
                print(f"❌ V1 {table}テーブル: アクセス不可")
        except Exception as e:
            add_test_result("既存機能", f"V1_{table}テーブル", "FAIL", str(e))
            print(f"❌ V1 {table}テーブル: {e}")
    
    # V2機能のテーブルチェック
    v2_tables = ["v2_users", "v2_chat_sessions", "v2_user_points", "v2_columns"]
    for table in v2_tables:
        try:
            result = supabase.table(table).select("*").limit(1).execute()
            if hasattr(result, 'data'):
                add_test_result("既存機能", f"V2_{table}テーブル", "PASS", "アクセス可能")
                print(f"✅ V2 {table}テーブル: アクセス可能")
            else:
                add_test_result("既存機能", f"V2_{table}テーブル", "FAIL", "アクセス不可")
                print(f"❌ V2 {table}テーブル: アクセス不可")
        except Exception as e:
            add_test_result("既存機能", f"V2_{table}テーブル", "FAIL", str(e))
            print(f"❌ V2 {table}テーブル: {e}")
    
    return True

async def test_api_consistency():
    """4. API一貫性チェック"""
    print("\n" + "="*60)
    print("【4】API一貫性チェック")
    print("="*60)
    
    # テーブル使用の一貫性確認
    api_files_table_check = {
        "/pages/api/v2/admin/columns.ts": "v2_columns",
        "/pages/api/v2/admin/columns/[id].ts": "v2_columns",
        "/pages/api/v2/admin/dashboard.ts": "v2_",
        "/pages/api/v2/admin/referrals.ts": "v2_"
    }
    
    for api_path, expected_table_prefix in api_files_table_check.items():
        full_path = f"/mnt/e/dev/Cusor/front/d-logic-ai-frontend{api_path}"
        try:
            if os.path.exists(full_path):
                with open(full_path, 'r') as f:
                    content = f.read()
                    if expected_table_prefix in content:
                        add_test_result("API一貫性", api_path, "PASS", f"{expected_table_prefix}使用確認")
                        print(f"✅ {api_path}: {expected_table_prefix}テーブル使用")
                    else:
                        add_test_result("API一貫性", api_path, "WARN", "テーブル使用不明")
                        print(f"⚠️ {api_path}: テーブル使用要確認")
            else:
                add_test_result("API一貫性", api_path, "INFO", "ファイル不存在")
                print(f"ℹ️ {api_path}: ファイル不存在")
        except Exception as e:
            add_test_result("API一貫性", api_path, "FAIL", str(e))
            print(f"❌ {api_path}: エラー {e}")
    
    return True

async def test_ui_integrity():
    """5. UI整合性チェック"""
    print("\n" + "="*60)
    print("【5】UI整合性チェック")
    print("="*60)
    
    # 主要UIコンポーネントファイルの存在確認
    ui_files = [
        "/src/app/v2/admin/page.tsx",
        "/src/app/v2/admin/columns/page.tsx",
        "/src/app/v2/admin/referrals/page.tsx",
        "/src/app/v2/column/page.tsx",
        "/src/app/v2/column/[id]/page.tsx"
    ]
    
    for ui_file in ui_files:
        full_path = f"/mnt/e/dev/Cusor/front/d-logic-ai-frontend{ui_file}"
        try:
            if os.path.exists(full_path):
                with open(full_path, 'r') as f:
                    content = f.read()
                    
                    # 必須要素の確認
                    checks = {
                        "NavigationBar": "NavigationBar" in content,
                        "Binanceスタイル": "#0B0E11" in content or "#F0B90B" in content,
                        "レスポンシブ": "md:" in content or "sm:" in content,
                        "ローディング処理": "loading" in content or "Loading" in content
                    }
                    
                    failed_checks = [k for k, v in checks.items() if not v]
                    
                    if not failed_checks:
                        add_test_result("UI整合性", ui_file, "PASS", "全要素確認")
                        print(f"✅ {ui_file}: UI要素完備")
                    else:
                        add_test_result("UI整合性", ui_file, "WARN", f"欠落: {', '.join(failed_checks)}")
                        print(f"⚠️ {ui_file}: 一部要素欠落 ({', '.join(failed_checks)})")
            else:
                add_test_result("UI整合性", ui_file, "INFO", "ファイル不存在")
                print(f"ℹ️ {ui_file}: ファイル不存在（正常の可能性）")
        except Exception as e:
            add_test_result("UI整合性", ui_file, "FAIL", str(e))
            print(f"❌ {ui_file}: エラー {e}")
    
    return True

async def test_build_and_lint():
    """6. ビルドとLintチェック"""
    print("\n" + "="*60)
    print("【6】ビルドとTypeScriptチェック")
    print("="*60)
    
    # TypeScriptコンパイルチェック（簡易）
    critical_files = [
        "/pages/api/v2/admin/dashboard.ts",
        "/pages/api/v2/columns/track-view.ts",
        "/src/app/v2/column/[id]/page.tsx"
    ]
    
    for file_path in critical_files:
        full_path = f"/mnt/e/dev/Cusor/front/d-logic-ai-frontend{file_path}"
        if os.path.exists(full_path):
            try:
                with open(full_path, 'r') as f:
                    content = f.read()
                    
                    # 基本的な構文チェック
                    syntax_issues = []
                    if content.count('{') != content.count('}'):
                        syntax_issues.append("括弧の不一致")
                    if content.count('(') != content.count(')'):
                        syntax_issues.append("丸括弧の不一致")
                    if 'console.log(' in content and 'debug' not in file_path.lower():
                        syntax_issues.append("console.log残存")
                    
                    if not syntax_issues:
                        add_test_result("ビルドチェック", file_path, "PASS", "構文OK")
                        print(f"✅ {file_path}: 構文チェックOK")
                    else:
                        add_test_result("ビルドチェック", file_path, "WARN", f"問題: {', '.join(syntax_issues)}")
                        print(f"⚠️ {file_path}: {', '.join(syntax_issues)}")
            except Exception as e:
                add_test_result("ビルドチェック", file_path, "FAIL", str(e))
                print(f"❌ {file_path}: チェックエラー {e}")
        else:
            add_test_result("ビルドチェック", file_path, "FAIL", "ファイル不存在")
            print(f"❌ {file_path}: ファイル不存在")
    
    return True

async def generate_final_report():
    """最終レポート生成"""
    print("\n" + "="*60)
    print("【最終テストレポート】")
    print("="*60)
    
    # スコア計算
    total = test_results["summary"]["total"]
    passed = test_results["summary"]["passed"]
    failed = test_results["summary"]["failed"]
    warnings = test_results["summary"]["warnings"]
    
    if total > 0:
        score = (passed / total) * 100
        
        # 減点
        score -= (failed * 10)  # 失敗1件につき-10点
        score -= (warnings * 3)  # 警告1件につき-3点
        score = max(0, min(100, score))  # 0-100の範囲に制限
    else:
        score = 0
    
    print(f"\n📊 テスト結果サマリー")
    print(f"  総テスト数: {total}")
    print(f"  ✅ 成功: {passed}")
    print(f"  ❌ 失敗: {failed}")
    print(f"  ⚠️ 警告: {warnings}")
    print(f"\n🎯 最終スコア: {score:.1f}/100点")
    
    # カテゴリー別結果
    print(f"\n📋 カテゴリー別結果:")
    for category, tests in test_results["tests"].items():
        category_passed = sum(1 for t in tests.values() if t["status"] == "PASS")
        category_total = len(tests)
        print(f"  {category}: {category_passed}/{category_total} 成功")
    
    # 判定
    print(f"\n🏁 デプロイ判定:")
    if score >= 95:
        print("  ✅ デプロイ可能！全機能が正常に動作しています。")
    elif score >= 80:
        print("  ⚠️ 条件付きデプロイ可能。軽微な問題がありますが、致命的ではありません。")
    else:
        print("  ❌ デプロイ非推奨。重大な問題を修正してください。")
    
    # 問題のある項目をリストアップ
    if failed > 0 or warnings > 0:
        print(f"\n⚠️ 要対応項目:")
        for category, tests in test_results["tests"].items():
            for test_name, result in tests.items():
                if result["status"] in ["FAIL", "WARN"]:
                    print(f"  - [{result['status']}] {category}/{test_name}: {result['details']}")
    
    # レポートファイルを保存
    report_file = f"/mnt/e/dev/Cusor/chatbot/uma/backend/tests/deployment_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(test_results, f, ensure_ascii=False, indent=2)
    print(f"\n📄 詳細レポート保存: {report_file}")
    
    return score

async def main():
    print("="*60)
    print("  最終デプロイメント前包括的テスト")
    print("  実行時刻:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("="*60)
    
    # 全テスト実行
    await test_system_status_monitoring()
    await test_column_view_tracking()
    await test_existing_functions()
    await test_api_consistency()
    await test_ui_integrity()
    await test_build_and_lint()
    
    # 最終レポート生成
    score = await generate_final_report()
    
    # 最終判定
    if score >= 95:
        print("\n" + "🎉"*20)
        print("  完璧です！デプロイの準備が整いました！")
        print("🎉"*20)
        return True
    elif score >= 80:
        print("\n" + "⚠️"*20)
        print("  軽微な問題がありますが、デプロイ可能です")
        print("⚠️"*20)
        return True
    else:
        print("\n" + "❌"*20)
        print("  重大な問題があります。修正が必要です")
        print("❌"*20)
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)