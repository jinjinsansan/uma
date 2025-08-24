#!/usr/bin/env python3
"""
IMLogicの12項目スコア計算をデバッグ
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.imlogic_engine import IMLogicEngine

def debug_imlogic():
    """IMLogicの計算過程を詳しく調査"""
    print("=== IMLogic 12項目スコア デバッグ ===\n")
    
    # エンジン初期化
    engine = IMLogicEngine()
    
    # テストレースデータ
    race_data = {
        'venue': '新潟',
        'race_number': 1,
        'race_name': '3歳未勝利',
        'distance': '1200m',
        'track_condition': '良',
        'horses': ['メリザンド', 'ザタイムズ', 'ミルキープリンセス'],
        'jockeys': ['岩田望来', '大野拓弥', '原優介'],
        'posts': [1, 2, 3],
        'horse_numbers': [1, 2, 3]
    }
    
    # バランス型の重み（全て8.3%前後）
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
    
    # 距離適性100%の重み
    distance_weights = balanced_weights.copy()
    distance_weights['1_distance_aptitude'] = 100
    for key in distance_weights:
        if key != '1_distance_aptitude':
            distance_weights[key] = 0
    
    print("1. バランス型での計算")
    print("-" * 50)
    
    # テスト用に内部メソッドを直接呼び出し
    for horse_name in race_data['horses']:
        context = {
            'venue': race_data['venue'],
            'grade': '',
            'distance': race_data['distance'],
            'track_condition': race_data['track_condition']
        }
        
        # ModernDLogicEngineの結果を確認
        ilogic_result = engine.modern_engine.calculate_horse_score(
            horse_name=horse_name,
            context=context,
            enable_bayesian=True
        )
        
        print(f"\n{horse_name}のI-Logic結果:")
        print(f"  base_score: {ilogic_result.get('base_score', 'なし')}")
        print(f"  d_logic_scores: {ilogic_result.get('d_logic_scores', {})}")
        
        # 拡張ナレッジからデータを確認
        horse_data = engine.modern_engine.knowledge.get(horse_name, [])
        print(f"  拡張ナレッジのレース数: {len(horse_data) if isinstance(horse_data, list) else 0}")
        
        # 12項目を推定
        if isinstance(horse_data, list) and len(horse_data) >= 3:
            estimated_scores = engine._estimate_12_items_from_races(horse_data)
            print(f"  推定12項目スコア:")
            for key, value in estimated_scores.items():
                print(f"    {key}: {value:.1f}")

if __name__ == "__main__":
    debug_imlogic()