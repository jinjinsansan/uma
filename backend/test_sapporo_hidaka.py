#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
デュアルペースシステムのテスト - 札幌11R 日高S
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.viewlogic_engine import ViewLogicEngine

def test_sapporo_hidaka():
    """札幌11R 日高S[3勝クラス]のテスト"""
    
    # テストデータ
    race_info = {
        'venue': '札幌',
        'race_number': 11,
        'race_name': '日高S[3勝クラス]',
        'distance': '1500m',
        'track_condition': '稍'  # 稍重
    }
    
    horses = [
        'モンドデラモーレ', 'オーサムストローク', 'ウインレイアー', 'モズナナスター',
        'ゴールドサーベル', 'ファインライン', 'ラファドゥラ', 'ブランデーロック',
        'リラボニート', 'フォルテム', 'カヨウネンカ', 'エリーズダイヤ', 'アルトゥーム'
    ]
    
    print("="*60)
    print("札幌11R - 日高S[3勝クラス] 展開予想テスト")
    print("="*60)
    print(f"距離: {race_info['distance']}")
    print(f"馬場: {race_info['track_condition']}重")
    print(f"出走頭数: {len(horses)}頭")
    print()
    
    # ViewLogicエンジン初期化
    print("ViewLogicエンジン初期化中...")
    engine = ViewLogicEngine()
    
    # 展開予想実行
    print("\n展開予想実行中...")
    race_data = {
        'horses': horses,
        'venue': race_info['venue'],
        'race_number': race_info['race_number'],
        'race_name': race_info['race_name'],
        'distance': race_info['distance'],
        'track_condition': race_info['track_condition']
    }
    result = engine.predict_race_flow_advanced(race_data)
    
    if result['status'] == 'success':
        print("\n✅ 展開予想成功！")
        
        # ペース判定の確認
        pace_data = result['pace_prediction']
        print("\n【ペース判定】")
        print(f"  表示用ペース: {pace_data['pace']}")
        print(f"  内部計算用ペース: {pace_data.get('calculation_pace', 'N/A')}")
        print(f"  前半3F平均: {pace_data['zenhan_avg']:.2f}秒")
        print(f"  後半3F平均: {pace_data['kohan_avg']:.2f}秒")
        print(f"  確信度: {pace_data['confidence']}%")
        
        # 上位5頭の確認
        print("\n【予想上位5頭】")
        finish_positions = result['race_simulation']['finish']
        top5 = sorted(finish_positions, key=lambda x: x['position'])[:5]
        for i, horse in enumerate(top5, 1):
            print(f"  {i}位: {horse['horse_name']} (スコア: {horse['position']:.2f})")
        
        # 脚質分布
        print("\n【脚質分布】")
        styles = result['detailed_styles']
        for style_type, sub_styles in styles.items():
            total = sum(len(horses) for horses in sub_styles.values())
            if total > 0:
                print(f"  {style_type}: {total}頭")
                for sub_style, horse_list in sub_styles.items():
                    if horse_list:
                        print(f"    - {sub_style}: {', '.join(horse_list)}")
        
        # 展開適性スコア上位
        print("\n【展開適性スコア上位】")
        flow_scores = result['flow_matching']
        sorted_scores = sorted(flow_scores.items(), key=lambda x: x[1], reverse=True)[:5]
        for horse_name, score in sorted_scores:
            print(f"  {horse_name}: {score:.1f}点")
        
        # デュアルペースシステムの確認
        print("\n【デュアルペースシステム動作確認】")
        zenhan = pace_data['zenhan_avg']
        print(f"  前半3F: {zenhan:.2f}秒")
        
        # 閾値による判定の違いを表示
        if zenhan <= 33.5:
            calc = "超ハイペース"
        elif zenhan <= 34.0:
            calc = "ハイペース"
        elif zenhan <= 34.5:
            calc = "平均ペース"
        else:
            calc = "スローペース"
            
        if zenhan <= 35.0:
            disp = "超ハイペース"
        elif zenhan <= 36.0:
            disp = "ハイペース"
        elif zenhan <= 37.0:
            disp = "平均ペース"
        else:
            disp = "スローペース"
            
        print(f"  元の閾値(33.5/34.0/34.5)での判定: {calc}")
        print(f"  新しい閾値(35.0/36.0/37.0)での判定: {disp}")
        
        if pace_data.get('calculation_pace') != pace_data['pace']:
            print("\n  ✅ デュアルペースシステム正常動作")
            print(f"     的中率重視（内部）: {pace_data.get('calculation_pace')}")
            print(f"     多様性重視（表示）: {pace_data['pace']}")
        else:
            print("\n  ⚠️ 内部計算と表示が同じ")
            
    else:
        print(f"\n❌ エラー: {result.get('message', '不明なエラー')}")

if __name__ == "__main__":
    test_sapporo_hidaka()