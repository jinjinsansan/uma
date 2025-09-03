"""
V2チャットのレース外馬制御テスト
修正後の動作を確認
"""

import asyncio
import json
import httpx

async def test_out_of_scope_horse():
    """レース外の馬を入力してテスト"""
    
    # テスト用のレースデータ
    race_data = {
        "race_id": "test-race-001",
        "race_date": "2025-09-03",
        "venue": "東京",
        "race_number": 11,
        "race_name": "テストレース",
        "horses": ["ドウデュース", "イクイノックス", "リバティアイランド"],
        "jockeys": ["川田将雅", "横山武史", "菅原明良"],
        "posts": [1, 2, 3],
        "horse_numbers": [1, 2, 3],
        "distance": "2000",
        "track_condition": "良"
    }
    
    # AI ハンドラーを直接テスト
    from services.v2.ai_handler import V2AIHandler
    
    handler = V2AIHandler()
    
    print("=" * 50)
    print("V2チャット レース外馬制御テスト")
    print("=" * 50)
    print(f"テストレースの馬: {race_data['horses']}")
    
    # テスト1: レース外の馬名
    print("\n[テスト1] レース外の馬名を入力")
    print("入力: 'オルフェーヴルの分析をして'")
    
    result = await handler.process_message(
        message="オルフェーヴルの分析をして",
        race_data=race_data,
        ai_type=None,
        settings=None
    )
    
    print(f"結果:")
    print(f"  AI Type: {result.get('ai_type')}")
    print(f"  Sub Type: {result.get('sub_type')}")
    print(f"  Content: {result.get('content')}")
    
    # テスト2: レース内の馬名
    print("\n" + "=" * 50)
    print("[テスト2] レース内の馬名を入力")
    print("入力: 'ドウデュースの過去5走'")
    
    result2 = await handler.process_message(
        message="ドウデュースの過去5走",
        race_data=race_data,
        ai_type=None,
        settings=None
    )
    
    print(f"結果:")
    print(f"  AI Type: {result2.get('ai_type')}")
    print(f"  Sub Type: {result2.get('sub_type')}")
    print(f"  Content: {result2.get('content')[:100]}...")
    
    # テスト3: 他のレースへの言及
    print("\n" + "=" * 50)
    print("[テスト3] 他のレースへの言及")
    print("入力: '阪神10Rはどうですか？'")
    
    result3 = await handler.process_message(
        message="阪神10Rはどうですか？",
        race_data=race_data,
        ai_type=None,
        settings=None
    )
    
    print(f"結果:")
    print(f"  AI Type: {result3.get('ai_type')}")
    print(f"  Sub Type: {result3.get('sub_type')}")
    print(f"  Content: {result3.get('content')}")
    
    print("\n" + "=" * 50)
    print("テスト完了")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(test_out_of_scope_horse())