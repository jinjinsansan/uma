#!/usr/bin/env python3
"""
ナレッジに存在する馬でIMLogicをテスト
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.imlogic_engine import IMLogicEngine

def test_known_horses():
    """ナレッジに存在する馬でテスト"""
    print("=== IMLogic 既知の馬でのテスト ===\n")
    
    # エンジン初期化
    engine = IMLogicEngine()
    
    # ナレッジに存在することが確認された馬でテスト
    test_horses = ['イクイノックス', 'ドウデュース', 'ジャスティンパレス']
    
    # まずこれらの馬が拡張ナレッジに存在するか確認
    print("1. 拡張ナレッジの確認")
    print("-" * 50)
    for horse in test_horses:
        horse_data = engine.modern_engine.knowledge.get(horse, [])
        if isinstance(horse_data, list):
            print(f"{horse}: {len(horse_data)}レース")
        else:
            print(f"{horse}: データ形式エラー")
    
    # テストレースデータ
    race_data = {
        'venue': '東京',
        'race_number': 11,
        'race_name': '天皇賞秋',
        'distance': '2000m',
        'track_condition': '良',
        'horses': test_horses,
        'jockeys': ['C.ルメール', '武豊', '横山武史'],
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
    
    # 距離適性100%
    distance_weights = {
        '1_distance_aptitude': 100,
        '2_bloodline_evaluation': 0,
        '3_jockey_compatibility': 0,
        '4_trainer_evaluation': 0,
        '5_track_aptitude': 0,
        '6_weather_aptitude': 0,
        '7_popularity_factor': 0,
        '8_weight_impact': 0,
        '9_horse_weight_impact': 0,
        '10_corner_specialist': 0,
        '11_margin_analysis': 0,
        '12_time_index': 0
    }
    
    print("\n2. バランス型での分析")
    print("-" * 50)
    result1 = engine.analyze_race(race_data, 70, 30, balanced_weights)
    for r in result1['results'][:3]:
        print(f"{r['rank']}位: {r['horse']} - 総合{r['total_score']:.2f}点 (馬{r['horse_score']:.2f})")
    
    print("\n3. 距離適性100%での分析")
    print("-" * 50)
    result2 = engine.analyze_race(race_data, 70, 30, distance_weights)
    for r in result2['results'][:3]:
        print(f"{r['rank']}位: {r['horse']} - 総合{r['total_score']:.2f}点 (馬{r['horse_score']:.2f})")
    
    # スコアが変わったか確認
    print("\n4. スコア変化の確認")
    print("-" * 50)
    for i, horse in enumerate(test_horses):
        score1 = result1['results'][i]['horse_score']
        score2 = result2['results'][i]['horse_score']
        diff = score2 - score1
        print(f"{horse}: {score1:.2f} → {score2:.2f} (差: {diff:+.2f})")

if __name__ == "__main__":
    test_known_horses()