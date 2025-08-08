#!/usr/bin/env python3
"""エラーハンドリングのテスト"""

import asyncio
from api.chat import get_multiple_horses_analysis, extract_multiple_horse_names
from services.fast_dlogic_engine import FastDLogicEngine

async def test_error_handling():
    """エラーハンドリングのテスト"""
    
    print("=" * 60)
    print("エラーハンドリングテスト")
    print("=" * 60)
    
    # テストケース1: 空のリスト
    print("\n【テスト1: 空のリスト】")
    result = await get_multiple_horses_analysis([])
    print(f"ステータス: {result.get('status')}")
    print(f"メッセージ: {result.get('message')}")
    
    # テストケース2: 21頭以上
    print("\n【テスト2: 21頭以上】")
    many_horses = [f"テスト馬{i}" for i in range(25)]
    result = await get_multiple_horses_analysis(many_horses)
    print(f"ステータス: {result.get('status')}")
    print(f"メッセージ: {result.get('message')}")
    
    # テストケース3: 存在しない馬を含む
    print("\n【テスト3: 存在しない馬を含む】")
    mixed_horses = ["ヤマニンバロネス", "存在しない馬A", "サツキノジョウ", "架空の馬B", "レガレイラ"]
    result = await get_multiple_horses_analysis(mixed_horses)
    print(f"ステータス: {result.get('status')}")
    print(f"要求馬数: {result.get('requested_count')}")
    print(f"分析成功馬数: {result.get('analyzed_count')}")
    
    if result.get('status') == 'success':
        horses = result.get('analysis_result', {}).get('horses', [])
        print("\n分析結果:")
        for horse in horses:
            if 'error' in horse:
                print(f"  {horse.get('horse_name', 'Unknown')}: エラー - {horse.get('error')}")
            else:
                print(f"  {horse.get('horse_name', 'Unknown')}: {horse.get('total_score', 0):.2f}点")
    
    # テストケース4: すべて存在しない馬
    print("\n【テスト4: すべて存在しない馬】")
    non_existent = ["架空の馬1", "架空の馬2", "架空の馬3"]
    result = await get_multiple_horses_analysis(non_existent)
    print(f"ステータス: {result.get('status')}")
    print(f"要求馬数: {result.get('requested_count')}")
    print(f"分析成功馬数: {result.get('analyzed_count')}")

if __name__ == "__main__":
    asyncio.run(test_error_handling())