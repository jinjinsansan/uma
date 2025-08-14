#!/usr/bin/env python3
"""
MyLogic偏差値変換＋累乗方式のテストスクリプト
劇的な変化が起きることを確認
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from services.mylogic_calculator import MyLogicCalculator
from datetime import datetime
import json

def test_dramatic_changes():
    """劇的な変化のテスト"""
    print("\n=== 偏差値変換＋累乗方式テスト ===")
    
    calculator = MyLogicCalculator()
    
    # テストケース1: バランス型（全項目均等）
    weights_balanced = {
        "distance_aptitude": 8,
        "bloodline_evaluation": 8,
        "jockey_compatibility": 8,
        "trainer_evaluation": 8,
        "track_aptitude": 9,
        "weather_aptitude": 9,
        "popularity_factor": 9,
        "weight_impact": 9,
        "horse_weight_impact": 8,
        "corner_specialist_degree": 8,
        "margin_analysis": 8,
        "time_index": 8
    }
    
    # テストケース2: 血統重視型（極端な例）
    weights_bloodline = {
        "distance_aptitude": 0,
        "bloodline_evaluation": 100,
        "jockey_compatibility": 0,
        "trainer_evaluation": 0,
        "track_aptitude": 0,
        "weather_aptitude": 0,
        "popularity_factor": 0,
        "weight_impact": 0,
        "horse_weight_impact": 0,
        "corner_specialist_degree": 0,
        "margin_analysis": 0,
        "time_index": 0
    }
    
    # テストケース3: 人気度重視型（通常低い項目）
    weights_popularity = {
        "distance_aptitude": 0,
        "bloodline_evaluation": 0,
        "jockey_compatibility": 0,
        "trainer_evaluation": 0,
        "track_aptitude": 0,
        "weather_aptitude": 0,
        "popularity_factor": 100,
        "weight_impact": 0,
        "horse_weight_impact": 0,
        "corner_specialist_degree": 0,
        "margin_analysis": 0,
        "time_index": 0
    }
    
    # テスト馬（様々なスコアレンジ）
    test_horses = ["エフフォーリア", "ドウデュース", "イクイノックス", "ジャスティンパレス"]
    
    print("\n【バランス型での比較】")
    print("馬名 | 標準D-Logic | MyLogic(バランス) | 差分")
    print("-" * 60)
    
    balanced_results = []
    for horse in test_horses:
        result = calculator.calculate_with_custom_weights(horse, weights_balanced)
        if 'error' not in result:
            balanced_results.append(result)
            print(f"{result['horse_name']:　<12} | {result['standard_score']:>8.2f}点 | "
                  f"{result['mylogic_score']:>12.2f}点 | {result['score_difference']:>+6.2f}点")
    
    print("\n【血統重視型での比較】")
    print("馬名 | 標準D-Logic | MyLogic(血統100) | 差分 | 血統生スコア")
    print("-" * 75)
    
    bloodline_results = []
    for horse in test_horses:
        result = calculator.calculate_with_custom_weights(horse, weights_bloodline)
        if 'error' not in result:
            bloodline_results.append(result)
            # 血統の生スコアを取得
            blood_score = 0
            if 'individual_scores' in result:
                for key, score in result['individual_scores'].items():
                    if 'bloodline' in key:
                        blood_score = score
                        break
            
            print(f"{result['horse_name']:　<12} | {result['standard_score']:>8.2f}点 | "
                  f"{result['mylogic_score']:>12.2f}点 | {result['score_difference']:>+6.2f}点 | "
                  f"{blood_score:>6.1f}点")
    
    # 順位の変動を確認
    print("\n【順位変動の確認】")
    print("標準D-Logic順位:")
    balanced_sorted = sorted(balanced_results, key=lambda x: x['standard_score'], reverse=True)
    for i, result in enumerate(balanced_sorted):
        print(f"  {i+1}位: {result['horse_name']} ({result['standard_score']:.2f}点)")
    
    print("\n血統重視型順位:")
    bloodline_sorted = sorted(bloodline_results, key=lambda x: x['mylogic_score'], reverse=True)
    for i, result in enumerate(bloodline_sorted):
        print(f"  {i+1}位: {result['horse_name']} ({result['mylogic_score']:.2f}点)")
    
    # 人気度重視（通常低い項目での逆転）
    print("\n【人気度重視型での比較】")
    print("馬名 | 標準D-Logic | MyLogic(人気100) | 差分")
    print("-" * 60)
    
    for horse in test_horses:
        result = calculator.calculate_with_custom_weights(horse, weights_popularity)
        if 'error' not in result:
            print(f"{result['horse_name']:　<12} | {result['standard_score']:>8.2f}点 | "
                  f"{result['mylogic_score']:>12.2f}点 | {result['score_difference']:>+6.2f}点")

def test_extreme_cases():
    """極端なケースのテスト"""
    print("\n\n=== 極端なケーステスト ===")
    
    calculator = MyLogicCalculator()
    
    # 2項目だけに50点ずつ
    weights_two_items = {
        "distance_aptitude": 50,
        "bloodline_evaluation": 50,
        "jockey_compatibility": 0,
        "trainer_evaluation": 0,
        "track_aptitude": 0,
        "weather_aptitude": 0,
        "popularity_factor": 0,
        "weight_impact": 0,
        "horse_weight_impact": 0,
        "corner_specialist_degree": 0,
        "margin_analysis": 0,
        "time_index": 0
    }
    
    # 全項目に少しずつ（でも偏りあり）
    weights_slight_bias = {
        "distance_aptitude": 20,
        "bloodline_evaluation": 15,
        "jockey_compatibility": 10,
        "trainer_evaluation": 10,
        "track_aptitude": 10,
        "weather_aptitude": 5,
        "popularity_factor": 5,
        "weight_impact": 5,
        "horse_weight_impact": 5,
        "corner_specialist_degree": 5,
        "margin_analysis": 5,
        "time_index": 5
    }
    
    test_horse = "エフフォーリア"
    
    print(f"\n【{test_horse}の各種パターン】")
    
    # バランス型の重み付けを定義（ここで必要）
    weights_balanced = {
        "distance_aptitude": 8,
        "bloodline_evaluation": 8,
        "jockey_compatibility": 8,
        "trainer_evaluation": 8,
        "track_aptitude": 9,
        "weather_aptitude": 9,
        "popularity_factor": 9,
        "weight_impact": 9,
        "horse_weight_impact": 8,
        "corner_specialist_degree": 8,
        "margin_analysis": 8,
        "time_index": 8
    }
    
    # 標準
    result = calculator.calculate_with_custom_weights(test_horse, weights_balanced)
    print(f"標準D-Logic: {result['standard_score']:.2f}点")
    
    # 2項目50点ずつ
    result = calculator.calculate_with_custom_weights(test_horse, weights_two_items)
    print(f"距離50+血統50: {result['mylogic_score']:.2f}点")
    
    # 微妙な偏り
    result = calculator.calculate_with_custom_weights(test_horse, weights_slight_bias)
    print(f"微妙な偏り: {result['mylogic_score']:.2f}点")

def test_score_distribution():
    """スコア分布の確認"""
    print("\n\n=== スコア分布テスト ===")
    
    calculator = MyLogicCalculator()
    
    # 多数の馬でテスト
    test_horses = [
        "エフフォーリア", "ドウデュース", "イクイノックス", "ジャスティンパレス",
        "タイトルホルダー", "パンサラッサ", "ジャックドール", "ダノンベルーガ",
        "スターズオンアース", "リバティアイランド", "ソングライン", "ドルチェモア"
    ]
    
    # 血統100点でのスコア分布
    weights_bloodline = {
        "distance_aptitude": 0,
        "bloodline_evaluation": 100,
        "jockey_compatibility": 0,
        "trainer_evaluation": 0,
        "track_aptitude": 0,
        "weather_aptitude": 0,
        "popularity_factor": 0,
        "weight_impact": 0,
        "horse_weight_impact": 0,
        "corner_specialist_degree": 0,
        "margin_analysis": 0,
        "time_index": 0
    }
    
    results = []
    for horse in test_horses:
        result = calculator.calculate_with_custom_weights(horse, weights_bloodline)
        if 'error' not in result:
            results.append({
                'name': result['horse_name'],
                'standard': result['standard_score'],
                'mylogic': result['mylogic_score']
            })
    
    # スコア順にソート
    results.sort(key=lambda x: x['mylogic'], reverse=True)
    
    print("\n血統重視型でのスコア分布:")
    print("順位 | 馬名 | MyLogicスコア | 標準スコア")
    print("-" * 50)
    
    for i, r in enumerate(results):
        print(f"{i+1:>2}位 | {r['name']:　<12} | {r['mylogic']:>8.2f}点 | {r['standard']:>8.2f}点")
    
    # スコアの分布を確認
    scores = [r['mylogic'] for r in results]
    print(f"\n最高点: {max(scores):.2f}点")
    print(f"最低点: {min(scores):.2f}点")
    print(f"平均点: {sum(scores)/len(scores):.2f}点")
    print(f"点差: {max(scores) - min(scores):.2f}点")

if __name__ == "__main__":
    print("MyLogic偏差値変換＋累乗方式テスト開始")
    print("=" * 60)
    
    test_dramatic_changes()
    test_extreme_cases()
    test_score_distribution()
    
    print("\n" + "=" * 60)
    print("テスト完了")