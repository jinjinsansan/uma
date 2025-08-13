#!/usr/bin/env python3
"""
MyLogic計算の完全テスト
レガレイラでの分析とD-Logicとの比較テスト
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from services.mylogic_calculator import MyLogicCalculator
import json
import logging

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_mylogic_calculation():
    """MyLogic計算テスト"""
    
    print("=" * 50)
    print("MyLogic 完全テスト開始")
    print("=" * 50)
    
    # MyLogic計算エンジン初期化
    mylogic = MyLogicCalculator()
    
    # テスト用の重み付け（均等）
    equal_weights = {
        "distance_aptitude": 8,
        "bloodline_evaluation": 8,
        "jockey_compatibility": 9,
        "trainer_evaluation": 8,
        "track_aptitude": 8,
        "weather_aptitude": 8,
        "popularity_factor": 8,
        "weight_impact": 8,
        "horse_weight_impact": 9,
        "corner_specialist_degree": 8,
        "margin_analysis": 9,
        "time_index": 9
    }
    
    # カスタム重み付け（血統重視）
    bloodline_focused_weights = {
        "distance_aptitude": 5,
        "bloodline_evaluation": 20,
        "jockey_compatibility": 5,
        "trainer_evaluation": 10,
        "track_aptitude": 5,
        "weather_aptitude": 5,
        "popularity_factor": 5,
        "weight_impact": 5,
        "horse_weight_impact": 5,
        "corner_specialist_degree": 10,
        "margin_analysis": 15,
        "time_index": 10
    }
    
    # スピード重視
    speed_focused_weights = {
        "distance_aptitude": 10,
        "bloodline_evaluation": 5,
        "jockey_compatibility": 5,
        "trainer_evaluation": 5,
        "track_aptitude": 10,
        "weather_aptitude": 5,
        "popularity_factor": 5,
        "weight_impact": 5,
        "horse_weight_impact": 5,
        "corner_specialist_degree": 10,
        "margin_analysis": 10,
        "time_index": 25
    }
    
    # テスト対象馬
    test_horses = ["レガレイラ", "エフワンライデン", "ディープインパクト"]
    
    for i, horse_name in enumerate(test_horses):
        print(f"\n{i+1}. 【{horse_name}】の分析")
        print("-" * 30)
        
        # 1. 均等重み付けテスト
        print("\n■ 均等重み付け")
        result_equal = mylogic.calculate_with_custom_weights(horse_name, equal_weights)
        print_result(result_equal)
        
        # 2. 血統重視テスト
        print("\n■ 血統重視重み付け")
        result_bloodline = mylogic.calculate_with_custom_weights(horse_name, bloodline_focused_weights)
        print_result(result_bloodline)
        
        # 3. スピード重視テスト
        print("\n■ スピード重視重み付け")
        result_speed = mylogic.calculate_with_custom_weights(horse_name, speed_focused_weights)
        print_result(result_speed)
        
        # 比較表示
        print(f"\n【比較結果】")
        print(f"  標準D-Logic: {result_equal.get('standard_score', 0)}")
        print(f"  均等重み  : {result_equal.get('mylogic_score', 0)} (差: {result_equal.get('score_difference', 0):+.1f})")
        print(f"  血統重視  : {result_bloodline.get('mylogic_score', 0)} (差: {result_bloodline.get('score_difference', 0):+.1f})")
        print(f"  スピード重視: {result_speed.get('mylogic_score', 0)} (差: {result_speed.get('score_difference', 0):+.1f})")
    
    # 重み付けのバリデーションテスト
    print(f"\n{'='*50}")
    print("重み付けバリデーションテスト")
    print(f"{'='*50}")
    
    # 合計が100でないケース
    invalid_weights = {
        "distance_aptitude": 10,
        "bloodline_evaluation": 10,
        "jockey_compatibility": 10,
        "trainer_evaluation": 10,
        "track_aptitude": 10,
        "weather_aptitude": 10,
        "popularity_factor": 10,
        "weight_impact": 10,
        "horse_weight_impact": 10,
        "corner_specialist_degree": 10,
        "margin_analysis": 10,
        "time_index": 10
    }  # 合計120
    
    print("\n■ 合計120の重み付けテスト（正規化されるか確認）")
    result_invalid = mylogic.calculate_with_custom_weights("レガレイラ", invalid_weights)
    print_result(result_invalid)

def print_result(result):
    """結果表示"""
    if "error" in result:
        print(f"エラー: {result['error']}")
        return
    
    print(f"  馬名: {result.get('horse_name', 'Unknown')}")
    print(f"  標準スコア: {result.get('standard_score', 0)}")
    print(f"  MyLogicスコア: {result.get('mylogic_score', 0)}")
    print(f"  差分: {result.get('score_difference', 0):+.1f}")
    print(f"  グレード: {result.get('grade', 'N/A')}")
    
    # 個別貢献度を表示（上位5項目のみ）
    contributions = result.get('individual_contributions', {})
    if contributions:
        sorted_items = sorted(contributions.items(), key=lambda x: x[1]['contribution'], reverse=True)
        print("  主要貢献項目:")
        for i, (key, data) in enumerate(sorted_items[:5]):
            japanese_name = get_japanese_name(key)
            print(f"    {i+1}. {japanese_name}: {data['contribution']:.1f} (重み{data['weight']}%)")

def get_japanese_name(english_key):
    """英語キーから日本語名に変換"""
    name_map = {
        "distance_aptitude": "距離適性",
        "bloodline_evaluation": "血統評価",
        "jockey_compatibility": "騎手相性",
        "trainer_evaluation": "調教師評価",
        "track_aptitude": "トラック適性",
        "weather_aptitude": "天候適性",
        "popularity_factor": "人気要因",
        "weight_impact": "斤量影響",
        "horse_weight_impact": "馬体重影響",
        "corner_specialist_degree": "コーナー巧者度",
        "margin_analysis": "着差分析",
        "time_index": "タイム指数"
    }
    return name_map.get(english_key, english_key)

if __name__ == "__main__":
    try:
        test_mylogic_calculation()
        print(f"\n{'='*50}")
        print("テスト完了")
        print(f"{'='*50}")
        
    except Exception as e:
        logger.error(f"テストエラー: {e}")
        import traceback
        traceback.print_exc()