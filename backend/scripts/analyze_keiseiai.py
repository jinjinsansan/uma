#!/usr/bin/env python3
"""
京成杯AH（芝1600m）の期待値分析
"""

import numpy as np

# レースデータ
race_info = {
    'name': '京成杯AH',
    'distance': 1600,
    'course': '芝',
    'venue': '中山'
}

# 実際のオッズと人気
horses_data = {
    'ホウオウラスカーズ': {'odds': 89.5, 'popularity': 13, 'number': 1},
    'アスコルティアーモ': {'odds': 18.2, 'popularity': 10, 'number': 2},
    'ドロップオブライト': {'odds': 20.4, 'popularity': 11, 'number': 3},
    'ダイシンヤマト': {'odds': 7.5, 'popularity': 3, 'number': 4},
    'ニシノスーベニア': {'odds': 10.7, 'popularity': 4, 'number': 5},
    'アサヒ': {'odds': 188.8, 'popularity': 15, 'number': 6},
    'コントラポスト': {'odds': 6.7, 'popularity': 2, 'number': 7},
    'シヴァース': {'odds': 11.2, 'popularity': 5, 'number': 8},
    'ジューンオレンジ': {'odds': 16.1, 'popularity': 9, 'number': 9},
    'カラマティアノス': {'odds': 12.5, 'popularity': 6, 'number': 10},
    'エリカエクスプレス': {'odds': 2.8, 'popularity': 1, 'number': 11},
    'キタウイング': {'odds': 134.6, 'popularity': 14, 'number': 12},
    'ムーンプローブ': {'odds': 217.9, 'popularity': 16, 'number': 13},
    'タイムトゥヘヴン': {'odds': 12.9, 'popularity': 7, 'number': 14},
    'タシット': {'odds': 66.8, 'popularity': 12, 'number': 15},
    'タガノエルピーダ': {'odds': 13.3, 'popularity': 8, 'number': 16}
}

# エンジン評価
engine_results = {
    'D-Logic': {
        1: ('ダイシンヤマト', 75.0),
        2: ('エリカエクスプレス', 70.3),
        3: ('コントラポスト', 68.6),
        4: ('カラマティアノス', 67.9),
        5: ('シヴァース', 67.7),
        6: ('タガノエルピーダ', 62.0),
        7: ('アスコルティアーモ', 59.9),
        8: ('タシット', 56.6),
        9: ('ニシノスーベニア', 55.8),
        10: ('ジューンオレンジ', 55.1),
        11: ('ドロップオブライト', 53.1),
        12: ('ホウオウラスカーズ', 49.5)
    },
    'I-Logic': {
        1: ('ダイシンヤマト', 54.9),
        2: ('エリカエクスプレス', 50.9),
        3: ('カラマティアノス', 49.5),
        4: ('コントラポスト', 49.4),
        5: ('シヴァース', 47.6),
        6: ('アスコルティアーモ', 45.9),
        7: ('タガノエルピーダ', 44.0),
        8: ('ニシノスーベニア', 40.4),
        9: ('タシット', 39.3),
        10: ('ジューンオレンジ', 37.3),
        11: ('ドロップオブライト', 36.9),
        12: ('ホウオウラスカーズ', 34.1)
    },
    'ViewLogic': {
        1: 'タイムトゥヘヴン',
        2: 'ニシノスーベニア', 
        3: 'コントラポスト',
        4: 'ジューンオレンジ',
        5: 'タガノエルピーダ'
    }
}

# 実際の結果
actual_result = {
    '1st': ('ホウオウラスカーズ', 1, 89.5, 13),
    '2nd': ('ドロップオブライト', 3, 20.4, 11),
    '3rd': ('コントラポスト', 7, 6.7, 2)
}

def calculate_engine_score(horse_name):
    """各馬のエンジン推奨度を計算"""
    score = 0
    
    # D-Logic（35% - 1600mで重要）
    for rank, (name, point) in engine_results['D-Logic'].items():
        if name == horse_name:
            if rank <= 5:
                score += (6 - rank) / 5 * 0.35
            elif rank <= 10:
                score += (11 - rank) / 10 * 0.35 * 0.3
            else:
                score += 0.02 * 0.35
            break
    
    # I-Logic（35% - 騎手重視）
    for rank, (name, point) in engine_results['I-Logic'].items():
        if name == horse_name:
            if rank <= 5:
                score += (6 - rank) / 5 * 0.35
            elif rank <= 10:
                score += (11 - rank) / 10 * 0.35 * 0.3
            else:
                score += 0.02 * 0.35
            break
    
    # ViewLogic（30% - 1600mでは中程度）
    for rank, name in enumerate(engine_results['ViewLogic'].values(), 1):
        if name == horse_name:
            score += (6 - rank) / 5 * 0.30
            break
    
    return score

def calculate_fair_value(odds, popularity):
    """フェア値の計算"""
    if popularity <= 3:
        return 0.65  # 人気馬は大幅に割高
    elif popularity <= 6:
        return 0.95  # 中位はやや割高
    elif popularity <= 10:
        return 1.25  # 中穴は割安
    else:
        return 1.35  # 大穴は割安だが不確実性高い

def calculate_distance_factor(horse_name, distance):
    """距離適性の計算"""
    # 1600mは中距離、バランス型
    base_factor = 1.0
    
    # ViewLogic上位馬には少しボーナス
    if horse_name in ['タイムトゥヘヴン', 'ニシノスーベニア']:
        base_factor = 1.1
    
    return base_factor

def analyze_expectation():
    """期待値分析"""
    print("=" * 60)
    print("京成杯AH 期待値分析")
    print("=" * 60)
    print(f"距離: {race_info['distance']}m {race_info['course']}")
    print(f"会場: {race_info['venue']}")
    
    # 各馬の期待値計算
    expectation_results = {}
    
    for horse_name, data in horses_data.items():
        # エンジン推奨度
        engine_score = calculate_engine_score(horse_name)
        
        # フェア値
        fair_value = calculate_fair_value(data['odds'], data['popularity'])
        
        # 距離適性
        distance_factor = calculate_distance_factor(horse_name, race_info['distance'])
        
        # 統合スコア（1600mでの重み付け）
        combined_score = (
            fair_value * 0.30 +        # フェア値の重み
            engine_score * 0.50 +      # エンジン評価の重み
            distance_factor * 0.20     # 距離適性の重み
        )
        
        # 期待値
        expectation = combined_score * data['odds']
        
        expectation_results[horse_name] = {
            'number': data['number'],
            'odds': data['odds'],
            'popularity': data['popularity'],
            'engine_score': engine_score,
            'fair_value': fair_value,
            'distance_factor': distance_factor,
            'combined_score': combined_score,
            'expectation': expectation
        }
    
    # 期待値でソート
    sorted_results = sorted(expectation_results.items(), 
                           key=lambda x: x[1]['expectation'], reverse=True)
    
    print("\n【期待値ランキング】")
    print("-" * 60)
    
    for rank, (name, data) in enumerate(sorted_results[:10], 1):
        # 実際の結果との照合
        result_mark = ""
        if name == actual_result['1st'][0]:
            result_mark = " ◎1着"
        elif name == actual_result['2nd'][0]:
            result_mark = " ○2着"
        elif name == actual_result['3rd'][0]:
            result_mark = " ▲3着"
        
        print(f"{rank:2}位: {data['number']:2}番 {name:12} "
              f"({data['popularity']:2}番人気) "
              f"オッズ:{data['odds']:6.1f} "
              f"期待値:{data['expectation']:6.2f} "
              f"エンジン:{data['engine_score']:.2f}"
              f"{result_mark}")
    
    print("\n" + "=" * 60)
    print("【エンジン評価と実際の結果】")
    print("=" * 60)
    
    print("\n◆ D-Logic評価:")
    print(f"  1位 ダイシンヤマト → 4着")
    print(f"  2位 エリカエクスプレス → 11着")
    print(f"  3位 コントラポスト → 3着 ▲")
    print(f"  12位 ホウオウラスカーズ → 1着 ◎")
    
    print("\n◆ I-Logic評価:")
    print(f"  同様の傾向")
    
    print("\n◆ ViewLogic評価:")
    print(f"  1位 タイムトゥヘヴン → 14着")
    print(f"  2位 ニシノスーベニア → 5着")
    print(f"  3位 コントラポスト → 3着 ▲")
    
    print("\n" + "=" * 60)
    print("【分析結果】")
    print("=" * 60)
    
    print("\n1. 大波乱の結果")
    print("  13番人気ホウオウラスカーズが勝利（89.5倍）")
    print("  全エンジンで低評価→予測困難な結果")
    
    print("\n2. 期待値分析の限界")
    print("  エンジン評価が低い馬の突然の好走")
    print("  展開の綾や当日の調子が大きく影響")
    
    print("\n3. 中穴馬の価値")
    print("  ドロップオブライト（11番人気）が2着")
    print("  期待値上位の中穴馬には一定の妙味")
    
    print("\n【結論】")
    print("✅ 1600mではD-Logic/I-Logicのバランス重視が基本")
    print("✅ ただし大穴馬の激走は予測困難")
    print("✅ 期待値10以上の中穴馬を広く押さえる戦略が有効")
    print("✅ コントラポスト（3着）は各エンジンで上位評価")

if __name__ == "__main__":
    analyze_expectation()