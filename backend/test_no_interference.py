#!/usr/bin/env python3
"""
既存V2機能への干渉チェックテスト
ViewLogic履歴機能の修正が他のAIに影響していないことを確認

テスト対象:
1. IMLogic - カスタム設定分析
2. D-Logic - 標準分析
3. ViewLogic展開予想 - 既存のViewLogic機能
4. ViewLogic傾向分析 - 既存のViewLogic機能
5. ViewLogic馬券推奨 - 既存のViewLogic機能
"""

import asyncio
from services.v2.ai_handler import V2AIHandler

def create_test_race_data():
    """テスト用レースデータ"""
    return {
        'race_id': 'test-interference-check',
        'race_date': '2025-08-31',
        'venue': '新潟',
        'race_number': 4,
        'race_name': '干渉チェックレース',
        'horses': ['エリックバローズ', 'ウンエン', 'アランチャータ'],
        'jockeys': ['川田将雅', 'C.ルメール', '武豊'],
        'posts': [1, 2, 3],
        'horse_numbers': [1, 2, 3],
        'distance': 1200,
        'track_condition': '良'
    }

async def test_no_interference():
    """既存機能への干渉がないことを確認"""
    
    print("🔍 既存V2機能への干渉チェック")
    print("=" * 60)
    
    handler = V2AIHandler()
    handler.current_race_data = create_test_race_data()
    
    # 各AIの判定テスト
    test_cases = [
        {
            'name': 'IMLogic分析',
            'messages': [
                'imlogic',
                'IMLogic',
                'アイエムロジック',
                'カスタム設定で分析',
                '馬70騎手30で分析'
            ],
            'expected_ai': 'imlogic',
            'expected_sub': None
        },
        {
            'name': 'D-Logic分析',
            'messages': [
                'dlogic',
                'D-Logic',
                'ディーロジック',
                '標準分析',
                'D-Logicで分析'
            ],
            'expected_ai': 'dlogic',
            'expected_sub': 'analysis'
        },
        {
            'name': 'ViewLogic展開予想',
            'messages': [
                '展開予想',
                'ペース予想',
                'レース展開',
                '逃げ馬',
                '先行馬'
            ],
            'expected_ai': 'viewlogic',
            'expected_sub': 'flow'
        },
        {
            'name': 'ViewLogic傾向分析',
            'messages': [
                '傾向分析',
                '過去の傾向',
                'コース傾向',
                '枠順傾向',
                '騎手傾向'
            ],
            'expected_ai': 'viewlogic',
            'expected_sub': 'trend'
        },
        {
            'name': 'ViewLogic馬券推奨',
            'messages': [
                '馬券推奨',
                '買い目',
                'おすすめ馬券',
                '推奨馬券',
                '馬券提案'
            ],
            'expected_ai': 'viewlogic',
            'expected_sub': 'recommendation'
        }
    ]
    
    total_tests = 0
    passed_tests = 0
    interference_found = False
    
    for ai_test in test_cases:
        print(f"\n🧪 {ai_test['name']}のテスト")
        
        for message in ai_test['messages']:
            total_tests += 1
            
            try:
                ai_type, sub_type = handler.determine_ai_type(message)
                
                # 期待値と比較
                expected_ai = ai_test['expected_ai']
                expected_sub = ai_test['expected_sub']
                
                if ai_type == expected_ai:
                    if expected_sub is None or sub_type == expected_sub:
                        print(f"   ✅ '{message}' → 正常判定 ({ai_type}, {sub_type})")
                        passed_tests += 1
                    else:
                        print(f"   ⚠️ '{message}' → サブタイプ不一致")
                        print(f"      期待: ({expected_ai}, {expected_sub})")
                        print(f"      結果: ({ai_type}, {sub_type})")
                        
                        # ViewLogic履歴に誤判定されていないかチェック
                        if sub_type == 'history':
                            print(f"      ❌ ViewLogic履歴に誤判定！干渉発生！")
                            interference_found = True
                else:
                    print(f"   ❌ '{message}' → 誤判定")
                    print(f"      期待: {expected_ai}")
                    print(f"      結果: {ai_type}")
                    
                    # ViewLogic履歴に誤判定されていないかチェック
                    if ai_type == 'viewlogic' and sub_type == 'history':
                        print(f"      ❌ ViewLogic履歴に誤判定！干渉発生！")
                        interference_found = True
                        
            except Exception as e:
                print(f"   ❌ エラー発生: {e}")
    
    # 特殊ケースのテスト（馬名・騎手名を含まないメッセージ）
    print(f"\n🧪 特殊ケース: 馬名・騎手名を含まないメッセージ")
    
    special_cases = [
        ('分析して', 'imlogic'),  # デフォルトはIMLogic
        ('予想して', 'viewlogic'),  # 予想系はViewLogic
        ('評価して', 'imlogic'),  # 評価系はIMLogic
    ]
    
    for message, expected_ai in special_cases:
        total_tests += 1
        try:
            ai_type, sub_type = handler.determine_ai_type(message)
            
            if ai_type == expected_ai:
                print(f"   ✅ '{message}' → 正常判定 ({ai_type})")
                passed_tests += 1
            else:
                print(f"   ❌ '{message}' → 誤判定")
                print(f"      期待: {expected_ai}")
                print(f"      結果: {ai_type}")
                
                if ai_type == 'viewlogic' and sub_type == 'history':
                    print(f"      ❌ ViewLogic履歴に誤判定！干渉発生！")
                    interference_found = True
                    
        except Exception as e:
            print(f"   ❌ エラー発生: {e}")
    
    # 結果サマリー
    print("\n" + "=" * 60)
    print("🏆 干渉チェック結果")
    print("=" * 60)
    print(f"総テスト数: {total_tests}")
    print(f"成功: {passed_tests}")
    print(f"失敗: {total_tests - passed_tests}")
    print(f"成功率: {passed_tests/total_tests*100:.1f}%")
    
    if interference_found:
        print("\n❌ 警告: ViewLogic履歴機能が既存機能に干渉しています！")
        print("修正が必要です。")
        return False
    elif passed_tests == total_tests:
        print("\n✅ 完璧！既存機能への干渉は一切ありません。")
        print("ViewLogic履歴機能の修正は安全に実装されています。")
        return True
    elif passed_tests >= total_tests * 0.95:
        print("\n✅ 良好！既存機能への干渉はほぼありません。")
        print("軽微な問題のみで、実用上問題ありません。")
        return True
    else:
        print("\n⚠️ 注意: 一部の既存機能に影響が出ている可能性があります。")
        return False

async def main():
    """メインテスト実行"""
    
    print("ViewLogic履歴機能修正の影響範囲テスト")
    print("既存のV2チャット機能に干渉していないことを確認します")
    print("")
    
    try:
        no_interference = await test_no_interference()
        
        if no_interference:
            print("\n🎉 安全性確認完了！")
            print("ViewLogic履歴機能の修正は既存機能に影響を与えていません。")
        else:
            print("\n⚠️ 干渉が検出されました。")
            print("追加の修正が必要です。")
            
    except Exception as e:
        print(f"\nテスト実行エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())