#!/usr/bin/env python3
"""
ModernDLogicEngineが使用しているナレッジファイルを確認
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.fast_dlogic_engine import FastDLogicEngine
from services.modern_dlogic_engine import ModernDLogicEngine
from services.race_analysis_engine import get_race_analysis_engine

def test_knowledge():
    """各エンジンのナレッジデータを確認"""
    print("=== ModernDLogicEngine ナレッジ確認 ===\n")
    
    # 1. FastDLogicEngine（通常）の作成
    print("1. FastDLogicEngineを作成...")
    fast_engine = FastDLogicEngine()
    if hasattr(fast_engine, 'raw_manager') and hasattr(fast_engine.raw_manager, 'knowledge_data'):
        normal_horses = fast_engine.raw_manager.knowledge_data.get('horses', {})
        print(f"   ✅ 通常ナレッジ: {len(normal_horses)}頭")
    else:
        print("   ❌ 通常ナレッジデータにアクセスできません")
    
    # 2. ModernDLogicEngineを作成
    print("\n2. ModernDLogicEngineを作成...")
    modern_engine = ModernDLogicEngine(fast_engine)
    print(f"   ✅ Modernエンジンのナレッジ: {len(modern_engine.knowledge)}頭")
    
    # データ形式を確認
    if modern_engine.knowledge:
        sample_horse = list(modern_engine.knowledge.keys())[0]
        sample_data = modern_engine.knowledge[sample_horse]
        if isinstance(sample_data, list):
            print(f"   データ形式: リスト（{len(sample_data)}レース）")
        elif isinstance(sample_data, dict):
            races = sample_data.get('races', [])
            print(f"   データ形式: 辞書（{len(races)}レース）")
    
    # 3. RaceAnalysisEngineを作成
    print("\n3. RaceAnalysisEngineを作成...")
    race_engine = get_race_analysis_engine(fast_engine)
    engine_knowledge = race_engine.modern_engine.knowledge
    print(f"   ✅ レース分析エンジンのナレッジ: {len(engine_knowledge)}頭")
    
    # どちらのナレッジを使用しているか判定
    print("\n4. 使用中のナレッジファイルを判定...")
    if len(engine_knowledge) > 60000:
        print("   ⚠️ 通常ナレッジファイル（63,392頭）を使用中")
        print("   → レース分析V2には拡張ナレッジファイル（38,000頭、9レース）が必要です")
    elif 30000 < len(engine_knowledge) < 40000:
        print("   ✅ 拡張ナレッジファイル（約38,000頭）を使用中")
    else:
        print(f"   ❓ 不明なナレッジファイル（{len(engine_knowledge)}頭）")

if __name__ == "__main__":
    test_knowledge()