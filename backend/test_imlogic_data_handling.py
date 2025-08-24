#!/usr/bin/env python3
"""
IMLogicのデータなし処理をテスト
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.imlogic_engine import IMLogicEngine

def test_data_handling():
    """データあり/なしの馬での動作確認"""
    print("=== IMLogic データハンドリングテスト ===\n")
    
    engine = IMLogicEngine()
    
    # テストレースデータ（データなしの馬を含む）
    race_data = {
        'venue': '新潟',
        'race_number': 1,
        'race_name': '3歳未勝利',
        'distance': '1200m',
        'track_condition': '良',
        'horses': [
            'メリザンド',          # データなし
            'ネポティズムベビー',  # 4レース（ベイズ推定）
            'イクイノックス'       # 9レース（通常計算）
        ],
        'jockeys': ['岩田望来', '津村明秀', 'C.ルメール'],
        'posts': [1, 2, 3],
        'horse_numbers': [1, 2, 3]
    }
    
    # バランス型
    balanced_weights = {
        '1_distance_aptitude': 8.3,
        '2_bloodline_evaluation': 8.3,
        '3_jockey_compatibility': 8.3,
        '4_trainer_evaluation': 8.3,
        '5_track_aptitude': 8.3,
        '6_weather_aptitude': 8.3,
        '7_popularity_factor': 8.3,
        '8_weight_impact': 8.3,
        '9_horse_weight_impact': 8.3,
        '10_corner_specialist': 8.4,
        '11_margin_analysis': 8.4,
        '12_time_index': 8.4
    }
    
    print("テスト: データなし・ベイズ推定・通常計算の混在")
    print("-" * 60)
    
    try:
        result = engine.analyze_race(race_data, 70, 30, balanced_weights)
        
        print(f"\n分析対象: {len(race_data['horses'])}頭")
        print(f"分析完了: {len(result['results'])}頭")
        print(f"データなしでスキップ: {len(race_data['horses']) - len(result['results'])}頭")
        
        print("\n結果:")
        for r in result['results']:
            print(f"{r['rank']}位: {r['horse']} - 総合{r['total_score']:.2f}点 (馬{r['horse_score']:.2f})")
            
    except Exception as e:
        print(f"エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_data_handling()