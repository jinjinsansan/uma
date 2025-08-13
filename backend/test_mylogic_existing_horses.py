#!/usr/bin/env python3
"""
ナレッジベース内の既存馬でのMyLogicテスト
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from services.mylogic_calculator import MyLogicCalculator
import logging

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_existing_horses():
    """既存馬でのMyLogicテスト"""
    
    print("=" * 50)
    print("既存馬でのMyLogic テスト")
    print("=" * 50)
    
    # MyLogic計算エンジン初期化
    mylogic = MyLogicCalculator()
    
    # バランス型重み付け
    balanced_weights = {
        "distance_aptitude": 10,
        "bloodline_evaluation": 10,
        "jockey_compatibility": 8,
        "trainer_evaluation": 8,
        "track_aptitude": 10,
        "weather_aptitude": 8,
        "popularity_factor": 6,
        "weight_impact": 6,
        "horse_weight_impact": 6,
        "corner_specialist_degree": 10,
        "margin_analysis": 10,
        "time_index": 8
    }
    
    # スピード特化重み付け
    speed_specialized_weights = {
        "distance_aptitude": 15,
        "bloodline_evaluation": 5,
        "jockey_compatibility": 5,
        "trainer_evaluation": 5,
        "track_aptitude": 15,
        "weather_aptitude": 5,
        "popularity_factor": 5,
        "weight_impact": 5,
        "horse_weight_impact": 5,
        "corner_specialist_degree": 5,
        "margin_analysis": 10,
        "time_index": 20
    }
    
    # テスト対象馬（ナレッジベース内にある馬名）
    test_horses = ["スマートバーベナ", "クロノスバローズ", "シーザワールド", "フレンドカグラ", "コウエイサムライ"]
    
    for i, horse_name in enumerate(test_horses):
        print(f"\n{i+1}. 【{horse_name}】の分析")
        print("-" * 40)
        
        # バランス型テスト
        result_balanced = mylogic.calculate_with_custom_weights(horse_name, balanced_weights)
        
        # スピード特化テスト  
        result_speed = mylogic.calculate_with_custom_weights(horse_name, speed_specialized_weights)
        
        if "error" not in result_balanced:
            print(f"📊 標準D-Logic    : {result_balanced['standard_score']:.1f}")
            print(f"⚖️ バランス型     : {result_balanced['mylogic_score']:.1f} ({result_balanced['grade']}) 差分: {result_balanced['score_difference']:+.1f}")
            print(f"🏃 スピード特化   : {result_speed['mylogic_score']:.1f} ({result_speed['grade']}) 差分: {result_speed['score_difference']:+.1f}")
            
            # 主要な強み項目表示
            contributions = result_balanced.get('individual_contributions', {})
            if contributions:
                sorted_items = sorted(contributions.items(), key=lambda x: x[1]['contribution'], reverse=True)
                print(f"💪 主要な強み:")
                for j, (key, data) in enumerate(sorted_items[:3]):
                    japanese_name = get_japanese_name(key)
                    print(f"   {j+1}. {japanese_name}: {data['contribution']:.1f}点")
        else:
            print(f"❌ エラー: {result_balanced['error']}")

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
        test_existing_horses()
        print(f"\n{'='*50}")
        print("✅ 既存馬テスト完了")
        print(f"{'='*50}")
        
    except Exception as e:
        logger.error(f"テストエラー: {e}")
        import traceback
        traceback.print_exc()