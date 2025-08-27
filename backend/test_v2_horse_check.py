#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V2 API 馬名チェック機能のテスト
"""

import asyncio
import json
from services.v2.ai_handler import V2AIHandler

async def test_horse_check():
    """馬名チェック機能のテスト"""
    
    # テスト用のレースデータ
    race_data = {
        'race_id': 'test-race-001',
        'race_date': '2025-08-27',
        'venue': '新潟',
        'race_number': 6,
        'race_name': 'テストレース',
        'horses': [
            'ドウデュース',
            'イクイノックス',
            'エフフォーリア',
            'ジャスティンパレス',
            'タイトルホルダー'
        ],
        'jockeys': ['武豊', 'C.ルメール', '川田将雅', '横山和生', '横山武史']
    }
    
    # AIハンドラーのインスタンス作成
    ai_handler = V2AIHandler()
    
    # テストケース1: レースに存在する馬
    print("=== テスト1: レースに存在する馬 ===")
    message1 = "ドウデュースの分析をして"
    is_out1 = ai_handler._is_out_of_scope(message1, race_data)
    print(f"メッセージ: {message1}")
    print(f"範囲外判定: {is_out1}")
    print()
    
    # テストケース2: レースに存在しない馬
    print("=== テスト2: レースに存在しない馬 ===")
    message2 = "コントレイルの分析をして"
    is_out2 = ai_handler._is_out_of_scope(message2, race_data)
    print(f"メッセージ: {message2}")
    print(f"範囲外判定: {is_out2}")
    
    if is_out2:
        # エラーメッセージの生成をシミュレート
        result = await ai_handler.process_message(
            message2, 
            race_data,
            ai_type='imlogic'
        )
        print(f"返却メッセージ: {result.get('content')}")
    print()
    
    # テストケース3: 複数の馬（一部存在しない）
    print("=== テスト3: 複数の馬（一部存在しない） ===")
    message3 = "ドウデュースとアーモンドアイを比較して"
    is_out3 = ai_handler._is_out_of_scope(message3, race_data)
    print(f"メッセージ: {message3}")
    print(f"範囲外判定: {is_out3}")
    
    if is_out3:
        result = await ai_handler.process_message(
            message3,
            race_data,
            ai_type='imlogic'
        )
        print(f"返却メッセージ: {result.get('content')}")
    print()
    
    # テストケース4: 他のレースへの言及
    print("=== テスト4: 他のレースへの言及 ===")
    message4 = "東京11Rの分析をして"
    is_out4 = ai_handler._is_out_of_scope(message4, race_data)
    print(f"メッセージ: {message4}")
    print(f"範囲外判定: {is_out4}")
    
    if is_out4:
        result = await ai_handler.process_message(
            message4,
            race_data,
            ai_type='imlogic'
        )
        print(f"返却メッセージ: {result.get('content')}")
    print()
    
    # テストケース5: 一般的な質問（馬名なし）
    print("=== テスト5: 一般的な質問 ===")
    message5 = "全馬分析して"
    is_out5 = ai_handler._is_out_of_scope(message5, race_data)
    print(f"メッセージ: {message5}")
    print(f"範囲外判定: {is_out5}")
    print()

if __name__ == "__main__":
    print("V2 馬名チェック機能テスト")
    print("=" * 50)
    asyncio.run(test_horse_check())
    print("\nテスト完了")