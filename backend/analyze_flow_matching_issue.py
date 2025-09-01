#!/usr/bin/env python3
"""
展開適性スコアの差別化問題を詳細分析
"""

from services.viewlogic_engine import ViewLogicEngine

def analyze_flow_matching_issue():
    """17頭での展開適性スコアを詳細分析"""
    
    print("="*70)
    print("展開適性スコアの差別化問題分析")
    print("="*70)
    
    engine = ViewLogicEngine()
    
    # 新潟記念のデータ（17頭）
    race_data = {
        'venue': '新潟',
        'race_number': 11,
        'horses': [
            'ブレイディヴェーグ', 'シェイクユアハート', 'グランドカリナン',
            'ナムラエイハブ', 'バレエマスター', 'クイーンズウォーク',
            'ダノンベルーガ', 'サスツルギ', 'ディープモンスター',
            'シンリョクカ', 'コスモフリーゲン', 'シランケド',
            'アスクドゥポルテ', 'アスクカムオンモア', 'エネルジコ',
            'ヴェローチェエラ', 'リフレーミング'
        ]
    }
    
    # 各馬のデータを取得
    horses_data = []
    for horse_name in race_data['horses']:
        horse_data = engine.data_manager.get_horse_data(horse_name)
        if horse_data:
            horses_data.append({
                'horse_name': horse_name,
                'data': horse_data
            })
    
    print(f"\n【データ取得状況】")
    print(f"出走頭数: {len(race_data['horses'])}頭")
    print(f"データ取得成功: {len(horses_data)}頭")
    
    # ペース予測
    pace_prediction = engine._advanced_pace_prediction([h['data'] for h in horses_data])
    print(f"\n【ペース予測】")
    print(f"予想ペース: {pace_prediction.get('pace')}")
    print(f"前半3F平均: {pace_prediction.get('zenhan_avg', 0):.1f}秒")
    
    # 各馬のスタイルインデックスを確認
    print(f"\n【各馬のスタイルインデックス】")
    style_indices = {}
    for horse in horses_data[:10]:  # 最初の10頭のみ表示
        horse_name = horse['horse_name']
        if 'races' in horse['data']:
            style_index = engine._calculate_style_index(horse['data']['races'])
            style_indices[horse_name] = style_index
            print(f"{horse_name:15}: {style_index:6.2f}")
    
    # フローマッチングスコアを計算
    flow_matching = engine._calculate_flow_matching([h['data'] for h in horses_data], pace_prediction)
    
    print(f"\n【展開適性スコアの分布】")
    scores = list(flow_matching.values())
    unique_scores = set(scores)
    
    # スコアの分布を分析
    score_distribution = {}
    for score in unique_scores:
        count = scores.count(score)
        score_distribution[score] = count
    
    for score, count in sorted(score_distribution.items(), reverse=True):
        print(f"  {score:.1f}点: {count}頭")
    
    print(f"\n【問題の分析】")
    print(f"ユニークなスコア数: {len(unique_scores)}種類")
    print(f"最高点: {max(scores):.1f}点")
    print(f"最低点: {min(scores):.1f}点")
    print(f"スコア範囲: {max(scores) - min(scores):.1f}点")
    
    # なぜ同じスコアになるのか分析
    print(f"\n【同一スコアの原因分析】")
    
    # データが取得できない馬を確認
    no_data_horses = []
    for horse_name in race_data['horses']:
        if horse_name not in flow_matching:
            no_data_horses.append(horse_name)
    
    if no_data_horses:
        print(f"データなし（デフォルト60点）: {len(no_data_horses)}頭")
        for horse in no_data_horses[:5]:
            print(f"  - {horse}")
    
    # スタイルインデックスが0の馬を確認
    zero_style_horses = [h for h, s in style_indices.items() if s == 0]
    if zero_style_horses:
        print(f"\nスタイルインデックス0の馬: {len(zero_style_horses)}頭")
        for horse in zero_style_horses[:5]:
            print(f"  - {horse}")
    
    print(f"\n【結論】")
    print("多くの馬が同じスコアになる理由：")
    print("1. ナレッジファイルにデータがない馬はデフォルト60点")
    print("2. 3Fタイムデータが欠損している馬は展開適性を計算できない")
    print("3. スローペースの場合、差別化の幅が小さい（±15%程度）")
    
if __name__ == "__main__":
    analyze_flow_matching_issue()