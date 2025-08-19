#!/usr/bin/env python3
"""
レース分析V2のデータ形式修正テストスクリプト
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.fast_dlogic_engine import FastDLogicEngine
from services.race_analysis_engine import get_race_analysis_engine
import json

def test_race_analysis():
    """修正後のレース分析をテスト"""
    print("=== レース分析V2 修正テスト ===\n")
    
    # テストデータ（新潟6R）
    race_data = {
        'venue': '新潟',
        'race_number': 6,
        'race_name': '中郷特別',
        'grade': '1勝',
        'distance': '1800m',
        'track_condition': '良',
        'horses': [
            'ラルンエベール',
            'クライスレリアーナ',
            'キューティリップ',
            'フォーカルフラワー',
            'メランジェ'
        ],
        'jockeys': [
            '川端',
            '津村',
            '江田照',
            '田辺',
            '丸山'
        ],
        'posts': [1, 2, 3, 4, 5],
        'horse_numbers': [1, 2, 3, 4, 6]
    }
    
    try:
        # エンジン初期化
        print("1. エンジン初期化中...")
        fast_engine = FastDLogicEngine()
        race_engine = get_race_analysis_engine(fast_engine)
        
        # レース分析実行
        print("\n2. レース分析実行中...")
        result = race_engine.analyze_race(race_data)
        
        # 結果表示
        if 'error' in result:
            print(f"\nエラー: {result['error']}")
        else:
            print(f"\n3. 分析結果（上位5頭）:")
            print("=" * 60)
            
            if 'results' in result:
                for i, horse_result in enumerate(result['results'][:5]):
                    print(f"\n{i+1}位: {horse_result['horse']} × {horse_result['jockey']}")
                    print(f"  総合スコア: {horse_result['total_score']:.1f}点")
                    print(f"  馬スコア: {horse_result.get('horse_score', 0):.1f}点")
                    print(f"  騎手スコア: {horse_result.get('jockey_score', 0):.1f}点")
                    
                # 全馬のスコアが同じでないことを確認
                scores = [h['horse_score'] for h in result['results']]
                unique_scores = set(scores)
                print(f"\n4. スコア分布確認:")
                print(f"  ユニークなスコア数: {len(unique_scores)}")
                print(f"  スコア範囲: {min(scores):.1f} - {max(scores):.1f}")
                
                if len(unique_scores) == 1:
                    print("  ⚠️ 警告: すべての馬が同じスコアです！")
                else:
                    print("  ✅ 成功: 馬ごとに異なるスコアが計算されています")
            
    except Exception as e:
        print(f"\nエラー発生: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_race_analysis()