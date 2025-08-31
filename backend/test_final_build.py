#!/usr/bin/env python3
"""
最終ビルドテスト
"""

import asyncio
from services.v2.ai_handler import V2AIHandler

async def test_final_build():
    """最終ビルドテスト"""
    
    print("🔧 最終ビルドテスト")
    print("=" * 50)
    
    # テスト用レースデータ
    race_data = {
        'race_id': 'build-test',
        'race_date': '2025-08-31',
        'venue': '新潟',
        'race_number': 11,
        'race_name': 'ビルドテストレース',
        'horses': ['ドウデュース', 'エフフォーリア'],
        'jockeys': ['武豊', 'C.ルメール'],
        'posts': [1, 2],
        'horse_numbers': [1, 2]
    }
    
    handler = V2AIHandler()
    handler.current_race_data = race_data
    
    tests_passed = 0
    tests_failed = 0
    
    # 1. IMLogicテスト
    try:
        ai_type, sub_type = handler.determine_ai_type("IMLogicで分析")
        if ai_type == 'imlogic':
            print("✅ IMLogic判定: OK")
            tests_passed += 1
        else:
            print(f"❌ IMLogic判定: NG ({ai_type})")
            tests_failed += 1
    except Exception as e:
        print(f"❌ IMLogic判定エラー: {e}")
        tests_failed += 1
    
    # 2. ViewLogic履歴テスト
    try:
        ai_type, sub_type = handler.determine_ai_type("ドウデュースの過去データ")
        if ai_type == 'viewlogic' and sub_type == 'history':
            print("✅ ViewLogic履歴判定: OK")
            tests_passed += 1
        else:
            print(f"❌ ViewLogic履歴判定: NG ({ai_type}/{sub_type})")
            tests_failed += 1
    except Exception as e:
        print(f"❌ ViewLogic履歴判定エラー: {e}")
        tests_failed += 1
    
    # 3. プログレスバーテスト
    try:
        content, result = await handler.process_viewlogic_message(
            "武豊騎手の過去データ",
            race_data,
            'history'
        )
        if "ViewLogic過去データを取得中" in content:
            print("✅ プログレスバー表示: OK")
            tests_passed += 1
        else:
            print("❌ プログレスバー表示: NG")
            tests_failed += 1
    except Exception as e:
        print(f"❌ プログレスバーエラー: {e}")
        tests_failed += 1
    
    print("\n" + "=" * 50)
    print(f"総テスト数: {tests_passed + tests_failed}")
    print(f"✅ 成功: {tests_passed}")
    print(f"❌ 失敗: {tests_failed}")
    
    if tests_failed == 0:
        print("\n🎉 ビルドテスト完了！デプロイ可能です。")
        return True
    else:
        print("\n⚠️ ビルドテストに問題があります。")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_final_build())
    exit(0 if result else 1)
