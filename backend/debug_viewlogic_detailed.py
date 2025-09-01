#!/usr/bin/env python3
"""
ViewLogicの各計算段階の詳細な値を確認
"""

from services.viewlogic_engine import ViewLogicEngine
import json

def debug_viewlogic():
    """各計算段階の値を詳しく確認"""
    
    # エンジン初期化
    engine = ViewLogicEngine()
    
    # テストレース
    test_race = {
        'venue': '新潟',
        'race_number': 2,
        'distance': '1800m',
        'horses': ['バッキンガムパレス', 'ヴィジブルライト', 'サトノアルタイル']
    }
    
    print("=== ViewLogic展開予想の計算フロー分析 ===\n")
    
    # まず馬データを取得
    horses_data = []
    for idx, horse_name in enumerate(test_race['horses'], 1):
        horse_data = engine.data_manager.get_horse_data(horse_name)
        if horse_data:
            horse_data['horse_number'] = idx
            horses_data.append(horse_data)
            
            # 各馬のレース数を確認
            if 'races' in horse_data:
                print(f"{horse_name}: {len(horse_data['races'])}レース分のデータあり")
                
                # 最新レースの前半3F・後半3Fを確認
                latest_race = horse_data['races'][0] if horse_data['races'] else None
                if latest_race:
                    zenhan = latest_race.get('ZENHAN_3F', 'なし')
                    kohan = latest_race.get('KOHAN_3F', 'なし')
                    print(f"  最新レース: 前半3F={zenhan}, 後半3F={kohan}")
            else:
                print(f"{horse_name}: レースデータなし")
    
    print("\n【1. ペース予測】")
    pace_prediction = engine._advanced_pace_prediction(horses_data)
    print(f"  pace: {pace_prediction.get('pace')}")
    print(f"  confidence: {pace_prediction.get('confidence')}")
    print(f"  zenhan_avg: {pace_prediction.get('zenhan_avg'):.2f}秒")
    print(f"  kohan_avg: {pace_prediction.get('kohan_avg'):.2f}秒")
    
    print("\n【2. 脚質指数の計算】")
    for horse_data in horses_data:
        if 'races' in horse_data:
            style_index = engine._calculate_style_index(horse_data['races'])
            print(f"  {horse_data['horse_name']}: style_index = {style_index:.2f}")
            print(f"    → {'差し・追込型' if style_index > 0 else '逃げ・先行型' if style_index < 0 else 'バランス型'}")
    
    print("\n【3. フローマッチング（展開適性）】")
    print(f"現在のペース: {pace_prediction.get('pace')}")
    
    # _calculate_flow_matchingの処理を手動で確認
    for horse_data in horses_data:
        horse_name = horse_data.get('horse_name', '不明')
        if 'races' in horse_data:
            style_index = engine._calculate_style_index(horse_data['races'])
            
            # 現在のロジックを再現
            pace = pace_prediction.get('pace')
            if 'ハイペース' in pace:
                if style_index > 0:
                    base_score = 65 + (style_index * 5)
                else:
                    base_score = 40 - (abs(style_index) * 3)
            elif 'スローペース' in pace:
                if style_index < 0:
                    base_score = 65 + (abs(style_index) * 5)
                else:
                    base_score = 40 - (style_index * 3)
            else:  # 平均ペース
                # ここが問題！！
                print(f"\n  ⚠️ {horse_name}は平均ペース処理に入りました")
                if hasattr(engine, '_calculate_performance_bonus'):
                    performance_bonus = engine._calculate_performance_bonus(horse_data['races'])
                else:
                    performance_bonus = 0  # 関数が存在しない！
                    print(f"    → performance_bonus関数が存在しません！デフォルト値0を使用")
                
                if abs(style_index) < 1:
                    base_score = 60 + performance_bonus
                elif style_index > 0:
                    base_score = 55 + (style_index * 2) + performance_bonus
                else:
                    base_score = 55 + (abs(style_index) * 2) + performance_bonus
            
            # ここも問題！performance_bonusを2回加算している
            final_score = base_score + performance_bonus if hasattr(engine, '_calculate_performance_bonus') else base_score
            final_score = min(100, max(0, final_score))
            
            print(f"  {horse_name}:")
            print(f"    style_index: {style_index:.2f}")
            print(f"    base_score: {base_score:.1f}")
            print(f"    final_score: {final_score:.1f}")

if __name__ == "__main__":
    debug_viewlogic()