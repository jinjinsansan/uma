#!/usr/bin/env python3
"""
多様性の問題をデバッグ
"""

import random
from services.viewlogic_engine import ViewLogicEngine

def test_diversity_debug():
    """多様性の問題を詳しく調査"""
    
    # ランダムが動作するか確認
    print("ランダムテスト:")
    for i in range(5):
        print(f"  {random.choice(['A', 'B', 'C', 'D'])}")
    
    engine = ViewLogicEngine()
    test_race = {
        'venue': '東京',
        'race_number': 11,
        'horses': ['ドウデュース', 'イクイノックス']
    }
    
    print("\n3回実行してformatted_outputの長さを確認:")
    for i in range(3):
        result = engine.predict_race_flow_advanced(test_race)
        if result.get('status') == 'success':
            formatted = result.get('formatted_output', '')
            print(f"  実行{i+1}: 長さ={len(formatted)}")
            if formatted:
                # 最初の異なる部分を探す
                lines = formatted.split('\n')
                for line in lines:
                    if '序盤' in line or 'スタート' in line or '各馬' in line:
                        print(f"    → {line[:60]}")
                        break
            else:
                print(f"    → formatted_outputが空")

if __name__ == "__main__":
    test_diversity_debug()