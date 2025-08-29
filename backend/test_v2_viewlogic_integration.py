#!/usr/bin/env python3
"""
V2システムでのViewLogic統合テスト
自然言語でのAI切り替えをテスト
"""

import sys
import os
import asyncio
import json

# プロジェクトのルートディレクトリをPythonパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.v2.ai_handler import V2AIHandler


def print_section(title):
    """セクションタイトルを表示"""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)


async def test_ai_determination():
    """AI判定テスト"""
    print_section("1. 自然言語からのAI判定テスト")
    
    handler = V2AIHandler()
    
    test_messages = [
        # ViewLogic展開予想
        ("今日のレースの展開を教えて", "viewlogic", "flow"),
        ("ペース予想をお願いします", "viewlogic", "flow"),
        ("逃げ馬はどれですか？", "viewlogic", "flow"),
        ("ハイペースになりそう？", "viewlogic", "flow"),
        
        # ViewLogic傾向分析
        ("東京2000mの傾向を教えて", "viewlogic", "trend"),
        ("騎手成績を見たい", "viewlogic", "trend"),
        ("このコースの血統傾向は？", "viewlogic", "trend"),
        
        # ViewLogic見解
        ("今日の見解を聞かせて", "viewlogic", "opinion"),
        ("おすすめの馬は？", "viewlogic", "opinion"),
        
        # IMLogic
        ("分析してください", "imlogic", "analysis"),
        ("評価をお願いします", "imlogic", "analysis"),
        
        # D-Logic
        ("D-Logic指数を見せて", "dlogic", "analysis"),
        ("12項目の評価は？", "dlogic", "analysis"),
        
        # I-Logic
        ("I-Logic分析をお願い", "ilogic", "analysis"),
        ("騎手を含めた総合評価", "ilogic", "analysis"),
    ]
    
    print("テストメッセージ数:", len(test_messages))
    correct = 0
    
    for message, expected_ai, expected_sub in test_messages:
        ai_type, sub_type = handler.determine_ai_type(message)
        
        if ai_type == expected_ai and sub_type == expected_sub:
            print(f"✅ 「{message}」 → {ai_type}/{sub_type}")
            correct += 1
        else:
            print(f"❌ 「{message}」")
            print(f"   期待: {expected_ai}/{expected_sub}")
            print(f"   実際: {ai_type}/{sub_type}")
    
    print(f"\n正答率: {correct}/{len(test_messages)} ({correct/len(test_messages)*100:.1f}%)")


async def test_viewlogic_flow_prediction():
    """ViewLogic展開予想のテスト"""
    print_section("2. ViewLogic展開予想の統合テスト")
    
    handler = V2AIHandler()
    
    # テスト用レースデータ
    race_data = {
        'venue': '東京',
        'race_number': 11,
        'race_name': 'テストレース',
        'distance': 2000,
        'course_type': '芝',
        'horses': [
            'ドウデュース',
            'イクイノックス',
            'ジャスティンパレス',
            'ダノンベルーガ',
            'ノースブリッジ'
        ]
    }
    
    # メッセージテスト
    test_messages = [
        "展開予想をしてください",
        "このレースのペースは？",
        "逃げ馬を教えて"
    ]
    
    for message in test_messages:
        print(f"\n📝 メッセージ: 「{message}」")
        
        result = await handler.process_message(
            message=message,
            race_data=race_data
        )
        
        print(f"AI種別: {result['ai_type']}")
        print(f"サブタイプ: {result['sub_type']}")
        print(f"\n応答内容:")
        print(result['content'][:500] + "..." if len(result['content']) > 500 else result['content'])
        
        if result.get('analysis_data'):
            print(f"\n分析データ: あり")


async def test_viewlogic_trend_analysis():
    """ViewLogicコース傾向分析のテスト"""
    print_section("3. ViewLogicコース傾向分析の統合テスト")
    
    handler = V2AIHandler()
    
    race_data = {
        'venue': '東京',
        'race_number': 11,
        'race_name': 'テストレース',
        'distance': 2000,
        'course_type': '芝',
        'horses': ['テスト馬A', 'テスト馬B']
    }
    
    message = "東京2000mの傾向を教えてください"
    
    result = await handler.process_message(
        message=message,
        race_data=race_data
    )
    
    print(f"📝 メッセージ: 「{message}」")
    print(f"AI種別: {result['ai_type']}")
    print(f"サブタイプ: {result['sub_type']}")
    print(f"\n応答内容:")
    print(result['content'])


async def test_viewlogic_daily_trend():
    """ViewLogic当日傾向（見解）のテスト"""
    print_section("4. ViewLogic当日傾向の統合テスト")
    
    handler = V2AIHandler()
    
    race_data = {
        'venue': '東京',
        'race_number': 11,
        'race_name': 'テストレース',
        'horses': ['テスト馬A', 'テスト馬B']
    }
    
    message = "今日の見解を聞かせてください"
    
    result = await handler.process_message(
        message=message,
        race_data=race_data
    )
    
    print(f"📝 メッセージ: 「{message}」")
    print(f"AI種別: {result['ai_type']}")
    print(f"サブタイプ: {result['sub_type']}")
    print(f"\n応答内容:")
    print(result['content'])


async def test_error_handling():
    """エラーハンドリングのテスト"""
    print_section("5. エラーハンドリングのテスト")
    
    handler = V2AIHandler()
    
    # 空のレースデータ
    empty_race_data = {
        'venue': '東京',
        'race_number': 1,
        'horses': []  # 空の馬リスト
    }
    
    message = "展開予想をお願いします"
    
    result = await handler.process_message(
        message=message,
        race_data=empty_race_data
    )
    
    print(f"📝 メッセージ: 「{message}」")
    print(f"空の馬リストでのテスト")
    print(f"AI種別: {result['ai_type']}")
    print(f"\n応答内容:")
    print(result['content'])
    
    # 存在しない馬でのテスト
    invalid_race_data = {
        'venue': '東京',
        'race_number': 1,
        'horses': ['存在しない馬A', '存在しない馬B']
    }
    
    result = await handler.process_message(
        message=message,
        race_data=invalid_race_data
    )
    
    print(f"\n存在しない馬でのテスト")
    print(f"応答内容:")
    print(result['content'])


async def main():
    """メイン実行関数"""
    print("\n" + "🏇"*30)
    print("  V2 ViewLogic統合テストスイート")
    print("🏇"*30)
    
    # 各テストを実行
    await test_ai_determination()
    await test_viewlogic_flow_prediction()
    await test_viewlogic_trend_analysis()
    await test_viewlogic_daily_trend()
    await test_error_handling()
    
    print("\n" + "="*60)
    print(" V2統合テスト完了")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())