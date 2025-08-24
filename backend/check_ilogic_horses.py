#!/usr/bin/env python3
"""
I-LogicとIMLogicで同じ馬がどう処理されているか確認
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.modern_dlogic_engine import ModernDLogicEngine
from services.fast_dlogic_engine import fast_engine_instance

def check_horses():
    """I-Logicで使われている馬の処理を確認"""
    print("=== I-Logic/IMLogicのナレッジ確認 ===\n")
    
    # ModernDLogicEngine初期化
    modern_engine = ModernDLogicEngine(fast_engine_instance)
    
    # テスト馬（I-Logicの結果にある馬）
    test_horses = [
        'ネポティズムベビー',
        'メリザンド', 
        'ミルキープリンセス',
        'ザタイムズ',
        'ヴィーナスゼファー'
    ]
    
    print("1. 拡張ナレッジ（34,388頭）での確認")
    print("-" * 60)
    for horse in test_horses:
        # 拡張ナレッジ
        extended_data = modern_engine.knowledge.get(horse, [])
        if isinstance(extended_data, list):
            print(f"  {horse}: {len(extended_data)}レース")
        else:
            print(f"  {horse}: データなし")
    
    print("\n2. 標準ナレッジ（63,392頭）での確認")
    print("-" * 60)
    for horse in test_horses:
        # 標準ナレッジ
        standard_knowledge = fast_engine_instance.raw_manager.knowledge_data.get('horses', {})
        if horse in standard_knowledge:
            horse_data = standard_knowledge[horse]
            race_count = horse_data.get('race_count', 0)
            print(f"  {horse}: {race_count}レース")
        else:
            print(f"  {horse}: データなし")
    
    print("\n3. I-Logicでの計算結果確認")
    print("-" * 60)
    
    context = {
        'venue': '新潟',
        'grade': '',
        'distance': '1200m', 
        'track_condition': '良'
    }
    
    for horse in test_horses[:3]:  # 上位3頭のみ
        result = modern_engine.calculate_horse_score(
            horse_name=horse,
            context=context,
            enable_bayesian=True
        )
        
        print(f"\n{horse}:")
        print(f"  base_score: {result.get('base_score', 0):.1f}")
        print(f"  estimation_method: {result.get('estimation_method', 'unknown')}")
        print(f"  data_confidence: {result.get('data_confidence', 'unknown')}")
        print(f"  d_logic_scores: {len(result.get('d_logic_scores', {}))}項目")

if __name__ == "__main__":
    check_horses()