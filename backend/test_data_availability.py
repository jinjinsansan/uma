#!/usr/bin/env python3
"""
問題の馬のデータ有無を確認
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.dlogic_raw_data_manager import dlogic_manager
from services.modern_dlogic_engine import ModernDLogicEngine
from services.fast_dlogic_engine import fast_engine_instance

def check_data_availability():
    """各ナレッジでのデータ有無を確認"""
    print("=== 馬データの有無確認 ===\n")
    
    # テスト馬
    test_horses = [
        'メリザンド',
        'ザタイムズ', 
        'ミルキープリンセス',
        'ネポティズムベビー',
        'ヴィーナスゼファー'
    ]
    
    # 1. 標準ナレッジ（63,392頭）
    print("1. 標準ナレッジ（63,392頭）")
    print("-" * 50)
    standard_knowledge = dlogic_manager.knowledge_data.get('horses', {})
    for horse in test_horses:
        if horse in standard_knowledge:
            data = standard_knowledge[horse]
            race_count = data.get('race_count', 0)
            print(f"  {horse}: {race_count}レース")
        else:
            print(f"  {horse}: データなし")
    
    # 2. 拡張ナレッジ（34,388頭）
    print("\n2. 拡張ナレッジ（34,388頭）")
    print("-" * 50)
    modern_engine = ModernDLogicEngine(fast_engine_instance)
    for horse in test_horses:
        data = modern_engine.knowledge.get(horse, [])
        if isinstance(data, list):
            print(f"  {horse}: {len(data)}レース")
        else:
            print(f"  {horse}: データなし")
    
    # 3. 推奨される対応
    print("\n3. 推奨される対応")
    print("-" * 50)
    print("選択肢1（推奨）: データがない馬は「分析不可」として扱う")
    print("  - 最も誠実で正確な対応")
    print("  - ユーザーに「ナレッジにデータがありません」と表示")
    print("\n選択肢2: 推定値で12項目に差をつける")
    print("  - データがなくても仮の値で計算")
    print("  - 重み変更で順位が変わるようになる")
    print("  - ただし精度は保証されない")

if __name__ == "__main__":
    check_data_availability()