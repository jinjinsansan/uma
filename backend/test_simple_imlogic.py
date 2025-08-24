#!/usr/bin/env python3
"""
IMLogicエンジンの直接テスト（Supabase依存なし）
"""
import asyncio
import json
from datetime import datetime

# IMLogicエンジンを直接インポート
from services.imlogic_engine import IMLogicEngine

async def test_imlogic_engine():
    """IMLogicエンジンの動作テスト"""
    print("🚀 IMLogicエンジン直接テスト")
    print("=" * 50)
    
    # テスト用のレースデータ
    race_data = {
        "venue": "東京",
        "race_number": 11,
        "race_name": "テスト記念（G2）",
        "horses": ["イクイノックス", "ドウデュース", "リバティアイランド", "ソダシ"],
        "jockeys": ["C.ルメール", "武豊", "川田将雅", "吉田隼人"],
        "posts": [1, 2, 3, 4],
        "horse_numbers": [1, 2, 3, 4]
    }
    
    # IMLogicエンジンのインスタンス作成
    engine = IMLogicEngine()
    
    # テスト1: デフォルト設定での分析
    print("\n1. デフォルト設定での分析")
    print("-" * 30)
    try:
        result = await engine.analyze_race(
            race_data=race_data,
            horse_weight=70,  # デフォルト
            jockey_weight=30, # デフォルト
            item_weights={
                "1_distance_aptitude": 8.33,
                "2_bloodline_evaluation": 8.33,
                "3_jockey_compatibility": 8.33,
                "4_trainer_evaluation": 8.33,
                "5_track_aptitude": 8.33,
                "6_weather_aptitude": 8.33,
                "7_popularity_factor": 8.33,
                "8_weight_impact": 8.33,
                "9_horse_weight_impact": 8.33,
                "10_corner_specialist": 8.33,
                "11_margin_analysis": 8.33,
                "12_time_index": 8.37
            }
        )
        
        print("✅ 分析成功")
        if 'results' in result:
            print("\n上位3頭:")
            for horse in result['results'][:3]:
                print(f"  {horse['rank']}位: {horse['horse']} ({horse['total_score']:.2f}点)")
                print(f"      馬スコア: {horse['horse_score']:.2f}点")
                print(f"      騎手スコア: {horse['jockey_score']:.2f}点")
        else:
            print(f"結果形式: {result.keys()}")
            
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()
    
    # テスト2: 血統重視設定での分析
    print("\n\n2. 血統重視設定での分析")
    print("-" * 30)
    try:
        result = await engine.analyze_race(
            race_data=race_data,
            horse_weight=80,
            jockey_weight=20,
            item_weights={
                "1_distance_aptitude": 5.0,
                "2_bloodline_evaluation": 40.0,  # 血統を40%重視
                "3_jockey_compatibility": 5.0,
                "4_trainer_evaluation": 5.0,
                "5_track_aptitude": 5.0,
                "6_weather_aptitude": 5.0,
                "7_popularity_factor": 5.0,
                "8_weight_impact": 5.0,
                "9_horse_weight_impact": 5.0,
                "10_corner_specialist": 5.0,
                "11_margin_analysis": 5.0,
                "12_time_index": 10.0
            }
        )
        
        print("✅ 分析成功")
        if 'results' in result:
            print("\n上位3頭:")
            for horse in result['results'][:3]:
                print(f"  {horse['rank']}位: {horse['horse']} ({horse['total_score']:.2f}点)")
                
    except Exception as e:
        print(f"❌ エラー: {e}")
    
    # テスト3: エンジンのメソッド確認
    print("\n\n3. エンジンのメソッド確認")
    print("-" * 30)
    print(f"IMLogicEngine メソッド: {[m for m in dir(engine) if not m.startswith('_')]}")
    print(f"FastDLogicEngine使用: {'fast_engine' in dir(engine)}")
    print(f"ナレッジデータ: {'horses_data' in dir(engine.fast_engine) if hasattr(engine, 'fast_engine') else 'N/A'}")

if __name__ == "__main__":
    asyncio.run(test_imlogic_engine())