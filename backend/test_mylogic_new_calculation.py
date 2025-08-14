#!/usr/bin/env python3
"""
MyLogic新計算式のテストスクリプト
新旧の計算方式を比較して、期待通りの差が出ることを確認
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from services.mylogic_calculator import MyLogicCalculator
from datetime import datetime
import json

def test_single_horse():
    """単一馬での計算テスト"""
    print("\n=== 単一馬テスト ===")
    
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
    
    # テストケース3: スピード重視型（距離適性＋タイム指数）
    weights_speed = {
        "distance_aptitude": 50,
        "bloodline_evaluation": 0,
        "jockey_compatibility": 0,
        "trainer_evaluation": 0,
        "track_aptitude": 0,
        "weather_aptitude": 0,
        "popularity_factor": 0,
        "weight_impact": 0,
        "horse_weight_impact": 0,
        "corner_specialist_degree": 0,
        "margin_analysis": 0,
        "time_index": 50
    }
    
    test_horse = "エフフォーリア"
    
    print(f"\n【{test_horse}】の分析結果：")
    
    # バランス型
    result1 = calculator.calculate_with_custom_weights(test_horse, weights_balanced)
    print(f"\n1. バランス型:")
    print(f"   標準D-Logic: {result1['standard_score']}点")
    print(f"   MyLogic: {result1['mylogic_score']}点")
    print(f"   差分: {result1['score_difference']}点")
    
    # 血統重視型
    result2 = calculator.calculate_with_custom_weights(test_horse, weights_bloodline)
    print(f"\n2. 血統重視型（血統100点）:")
    print(f"   標準D-Logic: {result2['standard_score']}点")
    print(f"   MyLogic: {result2['mylogic_score']}点")
    print(f"   差分: {result2['score_difference']}点")
    if 'individual_contributions' in result2:
        blood_score = result2['individual_contributions'].get('bloodline_evaluation', {})
        if blood_score:
            print(f"   血統評価の生スコア: {blood_score['original_score']}点")
    
    # スピード重視型
    result3 = calculator.calculate_with_custom_weights(test_horse, weights_speed)
    print(f"\n3. スピード重視型（距離50点＋タイム50点）:")
    print(f"   標準D-Logic: {result3['standard_score']}点")
    print(f"   MyLogic: {result3['mylogic_score']}点")
    print(f"   差分: {result3['score_difference']}点")
    if 'individual_contributions' in result3:
        dist_score = result3['individual_contributions'].get('distance_aptitude', {})
        time_score = result3['individual_contributions'].get('time_index', {})
        if dist_score and time_score:
            print(f"   距離適性の生スコア: {dist_score['original_score']}点")
            print(f"   タイム指数の生スコア: {time_score['original_score']}点")

def test_multiple_horses():
    """複数馬での計算テスト"""
    print("\n\n=== 複数馬テスト ===")
    
    calculator = MyLogicCalculator()
    
    # 血統重視型で複数馬を比較
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
    
    test_horses = ["エフフォーリア", "ドウデュース", "イクイノックス", "ジャスティンパレス"]
    
    print("\n【血統重視型での比較】")
    results = calculator.analyze_multiple_horses(test_horses, weights_bloodline)
    
    print("\n順位表:")
    print("順位 | 馬名 | 標準D-Logic | MyLogic(血統) | 差分")
    print("-" * 60)
    
    for i, result in enumerate(results):
        if 'error' not in result:
            print(f"{i+1}位 | {result['horse_name']:　<12} | {result['standard_score']:>8.2f}点 | {result['mylogic_score']:>10.2f}点 | {result['score_difference']:>+6.2f}点")

def test_calculation_time():
    """計算時間のテスト"""
    print("\n\n=== パフォーマンステスト ===")
    
    calculator = MyLogicCalculator()
    
    weights = {
        "distance_aptitude": 10,
        "bloodline_evaluation": 20,
        "jockey_compatibility": 5,
        "trainer_evaluation": 5,
        "track_aptitude": 10,
        "weather_aptitude": 5,
        "popularity_factor": 5,
        "weight_impact": 5,
        "horse_weight_impact": 5,
        "corner_specialist_degree": 10,
        "margin_analysis": 10,
        "time_index": 10
    }
    
    # 18頭でテスト
    test_horses = [
        "エフフォーリア", "ドウデュース", "イクイノックス", "ジャスティンパレス",
        "タイトルホルダー", "パンサラッサ", "ジャックドール", "ダノンベルーガ",
        "プログノーシス", "スターズオンアース", "リバティアイランド", "ソングライン",
        "ドルチェモア", "ウシュバテソーロ", "ノースブリッジ", "シャフリヤール",
        "レガレイラ", "サリエラ"
    ]
    
    start_time = datetime.now()
    results = calculator.analyze_multiple_horses(test_horses, weights)
    end_time = datetime.now()
    
    total_time = (end_time - start_time).total_seconds()
    
    print(f"\n{len(test_horses)}頭の分析時間: {total_time:.3f}秒")
    print(f"1頭あたり平均: {total_time/len(test_horses):.3f}秒")
    
    # エラーがあった馬を確認
    error_horses = [r for r in results if 'error' in r]
    if error_horses:
        print(f"\nエラーが発生した馬 ({len(error_horses)}頭):")
        for horse in error_horses:
            print(f"  - {horse['horse_name']}: {horse.get('error', '不明なエラー')}")

if __name__ == "__main__":
    print("MyLogic新計算式テスト開始")
    print("=" * 60)
    
    test_single_horse()
    test_multiple_horses()
    test_calculation_time()
    
    print("\n" + "=" * 60)
    print("テスト完了")