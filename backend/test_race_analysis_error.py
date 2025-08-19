#!/usr/bin/env python3
"""
レース分析エラーの再現テスト
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.race_analysis_engine import get_race_analysis_engine
from services.fast_dlogic_engine import FastDLogicEngine

def test_race_analysis():
    """レース分析の実行テスト"""
    print("=== レース分析エラー再現テスト ===\n")
    
    try:
        # 1. FastDLogicEngineの初期化
        print("1. FastDLogicEngineを初期化...")
        fast_engine = FastDLogicEngine()
        print("   成功")
        
        # 2. RaceAnalysisEngineの初期化
        print("\n2. RaceAnalysisEngineを初期化...")
        try:
            race_engine = get_race_analysis_engine(fast_engine)
            print("   成功")
        except Exception as e:
            print(f"   失敗: {e}")
            raise
        
        # 3. テストレースデータ
        print("\n3. テストレースデータを準備...")
        test_race = {
            'venue': '新潟',
            'race_number': 2,
            'race_name': '3歳未勝利',
            'distance': '2000m',
            'track_condition': '良',
            'horses': ['アカサカリゾート', 'クールジュジュ'],
            'jockeys': ['中村', 'ブローザ'],
            'posts': [1, 2],
            'horse_numbers': [1, 2]
        }
        print(f"   レース: {test_race['venue']}{test_race['race_number']}R")
        print(f"   出走馬: {test_race['horses']}")
        
        # 4. 分析実行
        print("\n4. レース分析を実行...")
        result = race_engine.analyze_race(test_race)
        
        if 'error' in result:
            print(f"   エラー: {result['error']}")
        else:
            print("   成功!")
            print(f"   結果数: {len(result.get('results', []))}")
            if result.get('results'):
                for i, horse_result in enumerate(result['results'][:2], 1):
                    print(f"\n   {i}位: {horse_result['horse']} × {horse_result['jockey']}")
                    print(f"      総合スコア: {horse_result['total_score']:.1f}点")
                    print(f"      馬スコア: {horse_result['horse_score']:.1f}点")
                    print(f"      騎手スコア: {horse_result['jockey_score']:.1f}点")
        
    except Exception as e:
        print(f"\nエラー発生: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_race_analysis()