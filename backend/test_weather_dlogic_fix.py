#!/usr/bin/env python3
"""
天候適性D-Logic修正後の動作確認テスト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.dlogic_raw_data_manager import dlogic_manager
import json

# テスト馬を選択
test_horses = ["ドウデュース", "イクイノックス", "ダンスインザダーク"]

print("=== 天候適性D-Logic 100点上限修正確認 ===")
print()

for horse_name in test_horses:
    print(f"\n【{horse_name}の分析】")
    
    # 標準D-Logic（良馬場）
    try:
        standard_result = dlogic_manager.calculate_dlogic_realtime(horse_name)
        if "error" not in standard_result:
            print(f"\n標準D-Logic（良馬場）:")
            print(f"  総合スコア: {standard_result['total_score']:.2f}点")
            print(f"  天候適性: {standard_result['d_logic_scores']['6_weather_aptitude']:.2f}点")
            
            # 天候適性D-Logic（不良馬場）
            weather_result = dlogic_manager.calculate_weather_adaptive_dlogic(horse_name, 4)
            if "error" not in weather_result:
                print(f"\n天候適性D-Logic（不良馬場）:")
                print(f"  総合スコア: {weather_result['total_score']:.2f}点 {'✅ 100点以下' if weather_result['total_score'] <= 100 else '❌ 100点超過'}")
                print(f"  天候適性: {weather_result['d_logic_scores']['6_weather_aptitude']:.2f}点 {'✅ 100点以下' if weather_result['d_logic_scores']['6_weather_aptitude'] <= 100 else '❌ 100点超過'}")
                print(f"  調整値: {weather_result['weather_adjustment']:.2f}点")
                
                # 階層評価の詳細
                details = weather_result['weather_details']
                print(f"\n  階層評価詳細:")
                print(f"    第1層（基礎能力）: {details['layer1_base_ability']:.2f}")
                print(f"    第2層（適応能力）: {details['layer2_adaptive_ability']:.2f}")
                print(f"    第3層（当日要因）: {details['layer3_daily_factors']:.2f}")
                print(f"    調整係数: {details['adjustment_factor']:.2f} {'✅ 範囲内' if 0.8 <= details['adjustment_factor'] <= 1.2 else '❌ 範囲外'}")
                
                # 個別項目の確認
                print(f"\n  個別項目の上限チェック:")
                over_100_items = []
                for key, score in weather_result['d_logic_scores'].items():
                    if score > 100:
                        over_100_items.append(f"{key}: {score:.2f}点")
                
                if over_100_items:
                    print(f"    ❌ 100点を超える項目: {', '.join(over_100_items)}")
                else:
                    print(f"    ✅ すべての項目が100点以下")
                    
        else:
            print(f"  エラー: {standard_result['error']}")
            
    except Exception as e:
        print(f"  エラー: {e}")

print("\n=== テスト完了 ===")