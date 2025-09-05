#!/usr/bin/env python3
"""
V2チャット フォーマティングテスト
D-Logic、IMLogic、I-Logicの表示形式が統一されているか確認
"""

import asyncio
import json
from services.v2.ai_handler import V2AIHandler

async def test_formatting():
    """各AIの出力フォーマットをテスト"""
    
    # テスト用レースデータ
    race_data = {
        'venue': '新潟',
        'race_number': 11,
        'race_name': '新潟記念',
        'horses': [
            'シランケド', 'ブレイディヴェーグ', 'コスモフリーゲン',
            'ヴェローチェエラ', 'アスクカムオンモア', 'クイーンズウォーク',
            'シェイクユアハート', 'ナムラエイハブ', 'グランドカリナン',
            'ディープモンスター', 'バレエマスター', 'シンリョクカ',
            'リフレーミング', 'サスツルギ', 'エネルジコ',
            'ダノンベルーガ', 'アスクドゥポルテ'
        ]
    }
    
    ai_handler = V2AIHandler()
    
    print("=" * 60)
    print("V2 AI フォーマットテスト")
    print("=" * 60)
    
    # 1. D-Logic テスト
    print("\n【D-Logic分析テスト】")
    print("-" * 40)
    try:
        result = await ai_handler.process_dlogic_message(
            message="このレースをD-Logicで分析して",
            race_data=race_data
        )
        print(result)
    except Exception as e:
        print(f"エラー: {e}")
    
    # 2. IMLogic テスト
    print("\n【IMLogic分析テスト】")
    print("-" * 40)
    try:
        result = await ai_handler.process_imlogic_message(
            message="このレースをIMLogicで分析して",
            race_data=race_data,
            settings=None
        )
        print(result)
    except Exception as e:
        print(f"エラー: {e}")
    
    # 3. I-Logic テスト（レース分析）
    print("\n【I-Logic分析テスト】")
    print("-" * 40)
    try:
        result = await ai_handler.process_ilogic_message(
            message="このレースをI-Logicで分析して",
            race_data=race_data
        )
        print(result)
    except Exception as e:
        print(f"エラー: {e}")
    
    print("\n" + "=" * 60)
    print("フォーマット確認ポイント:")
    print("1. すべて順位番号が表示されているか")
    print("2. 6位以降も順位が明記されているか")
    print("3. 行間が適切に空いているか")
    print("4. 表示が統一されているか")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_formatting())