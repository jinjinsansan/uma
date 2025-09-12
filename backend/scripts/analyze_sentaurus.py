#!/usr/bin/env python3
"""
阪神11RセントウルSの期待値分析
"""

import numpy as np

# エンジン分析結果
engine_results = {
    'D-Logic': {
        1: ('エコロジーク', 79.4),
        2: ('トウシンマカオ', 78.7),
        3: ('アブキールベイ', 76.1),
        4: ('ママコチャ', 72.1),
        5: ('ヨシノイースター', 70.6)
    },
    'I-Logic': {
        1: ('トウシンマカオ', 58.5),
        2: ('エコロジーク', 58.1),
        3: ('アブキールベイ', 55.7),
        4: ('ママコチャ', 52.8),
        5: ('ワンダーキサラ', 51.6)
    },
    'ViewLogic': {
        1: 'エコロジーク',
        2: 'アブキールベイ',
        3: 'テイエムスパーダ',
        4: 'ヨシノイースター',
        5: 'ウイングレイテスト'
    }
}

# 実際の結果
actual_result = {
    '1st': ('カンチェンジュンガ', 7, 19.4, 8),  # 馬名、馬番、オッズ、人気
    '2nd': ('ママコチャ', 3, 3.2, 2),
    '3rd': ('トウシンマカオ', 14, 2.5, 1)
}

# 仮定のオッズデータ（馬名とオッズ）
odds_data = {
    'トウシンマカオ': 2.5,
    'ママコチャ': 3.2,
    'エコロジーク': 5.5,  # 推定
    'アブキールベイ': 8.0,  # 推定
    'ヨシノイースター': 12.0,  # 推定
    'ワンダーキサラ': 15.0,  # 推定
    'カンチェンジュンガ': 19.4,
    'テイエムスパーダ': 25.0,  # 推定
    'ウイングレイテスト': 30.0  # 推定
}

def calculate_engine_score(horse_name):
    """各馬のエンジン推奨度を計算"""
    score = 0
    count = 0
    
    # D-Logic
    for rank, (name, point) in engine_results['D-Logic'].items():
        if name == horse_name:
            score += (6 - rank) / 5
            count += 1
            break
    
    # I-Logic
    for rank, (name, point) in engine_results['I-Logic'].items():
        if name == horse_name:
            score += (6 - rank) / 5
            count += 1
            break
    
    # ViewLogic
    for rank, name in enumerate(engine_results['ViewLogic'].values(), 1):
        if name == horse_name:
            score += (6 - rank) / 5
            count += 1
            break
    
    return score

def analyze_expectation():
    """期待値分析"""
    print("=" * 60)
    print("阪神11R セントウルS 期待値分析")
    print("=" * 60)
    
    # 各馬の統合スコアを計算
    horses_expectation = {}
    
    for horse_name, odds in odds_data.items():
        # エンジン推奨度
        engine_score = calculate_engine_score(horse_name)
        
        # フェア値（人気順位から推定）
        if odds <= 3.5:
            fair_value = 0.8  # 人気馬は割高傾向
        elif odds <= 10:
            fair_value = 1.0
        else:
            fair_value = 1.2  # 中穴は割安傾向
        
        # 統合期待値
        # 今回はエンジン推奨度を重視（前回の分析で有効と判明）
        combined_score = (fair_value * 0.3 + engine_score * 0.7)
        expectation = combined_score * odds
        
        horses_expectation[horse_name] = {
            'odds': odds,
            'engine_score': engine_score,
            'fair_value': fair_value,
            'expectation': expectation
        }
    
    # 期待値でソート
    sorted_horses = sorted(horses_expectation.items(), 
                          key=lambda x: x[1]['expectation'], reverse=True)
    
    print("\n【期待値ランキング】")
    for rank, (name, data) in enumerate(sorted_horses, 1):
        # 実際の結果との照合
        result_mark = ""
        if name == actual_result['1st'][0]:
            result_mark = " ◎1着"
        elif name == actual_result['2nd'][0]:
            result_mark = " ○2着"
        elif name == actual_result['3rd'][0]:
            result_mark = " ▲3着"
        
        print(f"{rank:2}位: {name:12} "
              f"オッズ:{data['odds']:5.1f} "
              f"期待値:{data['expectation']:5.2f} "
              f"エンジン評価:{data['engine_score']:.2f}"
              f"{result_mark}")
    
    print("\n" + "=" * 60)
    print("【エンジン評価と実際の結果】")
    print("=" * 60)
    
    # 各エンジンの的中状況
    print("\n◆ D-Logic上位5頭:")
    for rank, (name, point) in engine_results['D-Logic'].items():
        result = ""
        if name == actual_result['1st'][0]:
            result = " ◎1着"
        elif name == actual_result['2nd'][0]:
            result = " ○2着"
        elif name == actual_result['3rd'][0]:
            result = " ▲3着"
        print(f"  {rank}位: {name} ({point:.1f}点){result}")
    
    print("\n◆ I-Logic上位5頭:")
    for rank, (name, point) in engine_results['I-Logic'].items():
        result = ""
        if name == actual_result['1st'][0]:
            result = " ◎1着"
        elif name == actual_result['2nd'][0]:
            result = " ○2着"
        elif name == actual_result['3rd'][0]:
            result = " ▲3着"
        print(f"  {rank}位: {name} ({point:.1f}点){result}")
    
    print("\n◆ ViewLogic上位5頭:")
    for rank, name in enumerate(engine_results['ViewLogic'].values(), 1):
        result = ""
        if name == actual_result['1st'][0]:
            result = " ◎1着"
        elif name == actual_result['2nd'][0]:
            result = " ○2着"
        elif name == actual_result['3rd'][0]:
            result = " ▲3着"
        print(f"  {rank}位: {name}{result}")
    
    print("\n" + "=" * 60)
    print("【分析結果】")
    print("=" * 60)
    
    print(f"1着: カンチェンジュンガ（8番人気・19.4倍）")
    print(f"  → D-Logic 9位、I-Logic 7位、ViewLogic圏外")
    print(f"  → エンジン評価が低く、穴馬として予想困難")
    
    print(f"\n2着: ママコチャ（2番人気・3.2倍）")
    print(f"  → D-Logic 4位、I-Logic 4位、ViewLogic圏外")
    print(f"  → 2エンジンで推奨、妥当な評価")
    
    print(f"\n3着: トウシンマカオ（1番人気・2.5倍）")
    print(f"  → D-Logic 2位、I-Logic 1位、ViewLogic圏外")
    print(f"  → 上位評価も期待値は低い（人気馬の割高）")
    
    print("\n【考察】")
    print("1. ViewLogicが今回は不発（展開予想が外れた可能性）")
    print("2. カンチェンジュンガは川田騎手の好騎乗が影響")
    print("3. D-Logic/I-Logicの共通推奨馬（ママコチャ）は2着")
    print("4. 人気馬（トウシンマカオ）は3着で期待値通り低調")
    
    print("\n【改善提案】")
    print("・騎手能力の重み付けを増やす（川田騎手の場合+20%）")
    print("・ViewLogicの展開予想が外れた場合の補正")
    print("・複数エンジンで低評価の馬は期待値を下げる")

if __name__ == "__main__":
    analyze_expectation()