#!/usr/bin/env python3
"""
V2 AI Handlerのテストスクリプト
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.v2.ai_handler import V2AIHandler

# テスト用のレースデータ
test_race_data = {
    'venue': '東京',
    'race_number': 11,
    'race_name': '天皇賞（秋）',
    'race_date': '2024-10-27',
    'distance': '2000m',
    'track_condition': '良',
    'horses': [
        'ドウデュース',
        'イクイノックス',
        'ジャックドール',
        'プログノーシス',
        'スターズオンアース'
    ],
    'jockeys': [
        '戸崎圭太',
        'C.ルメール',
        '川田将雅',
        '横山典弘',
        '吉田豊'
    ],
    'posts': [1, 2, 3, 4, 5],
    'horse_numbers': [1, 2, 3, 4, 5]
}

async def test_determine_ai_type():
    """AIタイプ判定のテスト"""
    print("=" * 50)
    print("1. AI タイプ判定テスト")
    print("=" * 50)
    
    handler = V2AIHandler()
    
    test_cases = [
        ("このレースを分析して", "imlogic", "analysis"),
        ("D-Logicで分析して", "dlogic", "analysis"),
        ("I-Logic分析をお願い", "ilogic", "analysis"),
        ("傾向を教えて", "viewlogic", "trend"),
        ("見解を聞かせて", "viewlogic", "opinion"),
        ("評価して", "imlogic", "analysis"),  # デフォルト
    ]
    
    for message, expected_ai, expected_sub in test_cases:
        ai_type, sub_type = handler.determine_ai_type(message)
        status = "✅" if ai_type == expected_ai and sub_type == expected_sub else "❌"
        print(f"{status} '{message}' -> AI: {ai_type}, Sub: {sub_type}")
        if ai_type != expected_ai or sub_type != expected_sub:
            print(f"   期待値: AI: {expected_ai}, Sub: {expected_sub}")
    
    print()

async def test_process_message():
    """メッセージ処理のテスト"""
    print("=" * 50)
    print("2. メッセージ処理テスト")
    print("=" * 50)
    
    handler = V2AIHandler()
    
    test_messages = [
        "このレースを分析して",
        "D-Logicで分析して",
        "I-Logic分析して",
        "傾向を教えて"
    ]
    
    for message in test_messages:
        print(f"\nテスト: '{message}'")
        try:
            result = await handler.process_message(
                message=message,
                race_data=test_race_data
            )
            print(f"  AI Type: {result.get('ai_type')}")
            print(f"  Sub Type: {result.get('sub_type')}")
            print(f"  Content Length: {len(result.get('content', ''))} 文字")
            
            # 分析データの確認
            if result.get('analysis_data'):
                data = result['analysis_data']
                print(f"  Analysis Data Type: {data.get('type')}")
                if data.get('top_horses'):
                    print(f"  Top Horses: {data['top_horses'][:3]}")
                    
        except Exception as e:
            print(f"  ❌ エラー: {e}")
            import traceback
            traceback.print_exc()

async def test_dlogic_ilogic_batch():
    """D-Logic/I-Logicバッチ計算の直接テスト"""
    print("=" * 50)
    print("3. D-Logic/I-Logic バッチ計算テスト")
    print("=" * 50)
    
    # D-Logicバッチテスト
    print("\nD-Logic バッチ計算:")
    try:
        from api.v2.dlogic import calculate_dlogic_batch
        horses = test_race_data['horses'][:3]  # 3頭でテスト
        print(f"  テスト馬: {horses}")
        result = await calculate_dlogic_batch(horses)
        if result:
            for horse, data in result.items():
                print(f"  {horse}: {data.get('score', 'N/A')}点")
        else:
            print("  結果なし")
    except Exception as e:
        print(f"  ❌ エラー: {e}")
    
    # I-Logicバッチテスト
    print("\nI-Logic バッチ計算:")
    try:
        from api.v2.ilogic import calculate_ilogic_batch
        result = await calculate_ilogic_batch(
            horses=test_race_data['horses'][:3],
            jockeys=test_race_data['jockeys'][:3],
            posts=test_race_data['posts'][:3],
            horse_numbers=test_race_data['horse_numbers'][:3],
            venue=test_race_data['venue']
        )
        if result:
            for horse, data in result.items():
                print(f"  {horse}: 総合{data.get('score', 'N/A')}点 (馬:{data.get('horse_score', 'N/A')}, 騎手:{data.get('jockey_score', 'N/A')})")
        else:
            print("  結果なし")
    except Exception as e:
        print(f"  ❌ エラー: {e}")

async def main():
    print("\n" + "=" * 50)
    print("V2 AI Handler テスト開始")
    print("=" * 50 + "\n")
    
    # 1. AIタイプ判定テスト
    await test_determine_ai_type()
    
    # 2. メッセージ処理テスト
    await test_process_message()
    
    # 3. バッチ計算テスト
    await test_dlogic_ilogic_batch()
    
    print("\n" + "=" * 50)
    print("テスト完了")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())