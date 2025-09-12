#!/usr/bin/env python3
"""
エニフS（ダート1400m）の期待値分析
"""

import numpy as np

# レースデータ
race_info = {
    'name': 'エニフS',
    'distance': 1400,
    'course': 'ダート',
    'venue': '阪神'
}

# 実際のオッズと人気
horses_data = {
    'サフランヒーロー': {'odds': 13.8, 'popularity': 5, 'number': 1},
    'コンティノアール': {'odds': 12.2, 'popularity': 4, 'number': 2},
    'タイセイブレイズ': {'odds': 89.1, 'popularity': 12, 'number': 3},
    'ナナオ': {'odds': 25.7, 'popularity': 9, 'number': 4},
    'ノーブルロジャー': {'odds': 22.3, 'popularity': 8, 'number': 5},
    'ジョウショーホープ': {'odds': 76.6, 'popularity': 11, 'number': 6},
    'ベルダーイメル': {'odds': 179.7, 'popularity': 14, 'number': 7},
    'キャプテンネキ': {'odds': 18.8, 'popularity': 7, 'number': 8},
    'モズミギカタアガリ': {'odds': 6.9, 'popularity': 2, 'number': 9},
    'アルムラトゥール': {'odds': 101.7, 'popularity': 13, 'number': 10},
    'サンライズパスカル': {'odds': 56.4, 'popularity': 10, 'number': 11},
    'ライツフォル': {'odds': 8.0, 'popularity': 3, 'number': 12},
    'フルム': {'odds': 17.5, 'popularity': 6, 'number': 13},
    'インユアパレス': {'odds': 1.7, 'popularity': 1, 'number': 14}
}

# エンジン評価
engine_results = {
    'D-Logic': {
        1: ('インユアパレス', 73.0),
        2: ('ライツフォル', 72.6),
        3: ('サフランヒーロー', 72.3),
        4: ('モズミギカタアガリ', 69.0),
        5: ('コンティノアール', 65.7),
        6: ('タイセイブレイズ', 62.5),
        7: ('サンライズパスカル', 59.7),
        8: ('キャプテンネキ', 58.8),
        9: ('フルム', 55.9),
        10: ('ノーブルロジャー', 50.4),
        11: ('ジョウショーホープ', 48.4),
        12: ('ナナオ', 47.3),
        13: ('ベルダーイメル', 43.6),
        14: ('アルムラトゥール', 34.4)
    },
    'I-Logic': {
        1: ('インユアパレス', 56.9),
        2: ('ライツフォル', 55.0),
        3: ('サフランヒーロー', 52.8),
        4: ('モズミギカタアガリ', 50.3),
        5: ('コンティノアール', 47.9),
        6: ('タイセイブレイズ', 43.6),
        7: ('キャプテンネキ', 43.6),
        8: ('サンライズパスカル', 43.4),
        9: ('フルム', 40.7),
        10: ('ノーブルロジャー', 36.3),
        11: ('ジョウショーホープ', 34.9),
        12: ('ナナオ', 34.1),
        13: ('ベルダーイメル', 31.3),
        14: ('アルムラトゥール', 24.4)
    },
    'ViewLogic': {
        1: 'サフランヒーロー',
        2: 'フルム',
        3: 'インユアパレス',
        4: 'ノーブルロジャー',
        5: 'コンティノアール'
    }
}

# 実際の結果
actual_result = {
    '1st': ('インユアパレス', 14, 1.7, 1),
    '2nd': ('ライツフォル', 12, 8.0, 3),
    '3rd': ('モズミギカタアガリ', 9, 6.9, 2)
}

def calculate_engine_score(horse_name):
    """各馬のエンジン推奨度を計算（ダート戦用）"""
    score = 0
    
    # D-Logic（40% - ダートで最重要）
    for rank, (name, point) in engine_results['D-Logic'].items():
        if name == horse_name:
            if rank <= 5:
                score += (6 - rank) / 5 * 0.40
            elif rank <= 10:
                score += (11 - rank) / 10 * 0.40 * 0.3
            else:
                score += 0.02 * 0.40
            break
    
    # I-Logic（40% - ダートでは騎手重要）
    for rank, (name, point) in engine_results['I-Logic'].items():
        if name == horse_name:
            if rank <= 5:
                score += (6 - rank) / 5 * 0.40
            elif rank <= 10:
                score += (11 - rank) / 10 * 0.40 * 0.3
            else:
                score += 0.02 * 0.40
            break
    
    # ViewLogic（20% - ダートでは参考程度）
    for rank, name in enumerate(engine_results['ViewLogic'].values(), 1):
        if name == horse_name:
            score += (6 - rank) / 5 * 0.20
            break
    
    return score

def calculate_fair_value(odds, popularity):
    """ダート戦用のフェア値計算"""
    if popularity <= 3:
        return 0.75  # 人気馬はやや割高
    elif popularity <= 6:
        return 1.00  # 中位は適正
    elif popularity <= 10:
        return 1.20  # 中穴はやや割安
    else:
        return 1.10  # 大穴は不確実

def calculate_distance_factor(horse_name, distance):
    """ダート1400mの距離適性"""
    # ダート短距離、スピード重視
    base_factor = 1.0
    
    # D-Logic/I-Logic上位馬にボーナス
    if horse_name in ['インユアパレス', 'ライツフォル']:
        base_factor = 1.15
    elif horse_name in ['モズミギカタアガリ', 'コンティノアール']:
        base_factor = 1.10
    
    return base_factor

def analyze_expectation():
    """期待値分析"""
    print("=" * 60)
    print("エニフS 期待値分析")
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
        
        # 統合スコア（ダート戦用の重み付け）
        combined_score = (
            fair_value * 0.25 +        # フェア値の重み（ダートは低め）
            engine_score * 0.60 +      # エンジン評価の重み（ダートは高め）
            distance_factor * 0.15     # 距離適性の重み
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
    print(f"  1位 インユアパレス → 1着 ◎")
    print(f"  2位 ライツフォル → 2着 ○")
    print(f"  3位 サフランヒーロー → 12着")
    print(f"  4位 モズミギカタアガリ → 3着 ▲")
    
    print("\n◆ I-Logic評価:")
    print(f"  同様の傾向（川田騎手のインユアパレスが1位）")
    
    print("\n◆ ViewLogic評価:")
    print(f"  1位 サフランヒーロー → 12着")
    print(f"  2位 フルム → 9着")
    print(f"  3位 インユアパレス → 1着 ◎")
    
    print("\n" + "=" * 60)
    print("【分析結果】")
    print("=" * 60)
    
    print("\n1. 順当な結果")
    print("  1-3番人気が上位独占")
    print("  D-Logic/I-Logicが的中")
    
    print("\n2. ダート戦の特徴")
    print("  エンジン評価通りの堅い結果")
    print("  ViewLogicはダートで精度低下")
    
    print("\n3. 期待値の妥当性")
    print("  人気馬の期待値は低いが着順は良好")
    print("  ダートでは実力重視が有効")
    
    print("\n【結論】")
    print("✅ ダート1400mではD-Logic/I-Logic重視（各40%）")
    print("✅ ViewLogicは参考程度（20%）に留める")
    print("✅ 人気馬でもエンジン上位なら信頼できる")
    print("✅ 期待値より実力（エンジン評価）を重視すべき")

if __name__ == "__main__":
    analyze_expectation()