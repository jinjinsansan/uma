#!/usr/bin/env python3
"""
改善された展開適性スコアの差別化をテスト
"""

from services.viewlogic_engine import ViewLogicEngine

def test_improved_flow_matching():
    """改善後の展開適性スコアをテスト"""
    
    print("="*70)
    print("改善された展開適性スコアのテスト")
    print("="*70)
    
    engine = ViewLogicEngine()
    
    # 新潟記念のデータ（17頭）
    race_data = {
        'venue': '新潟',
        'race_number': 11,
        'race_name': '新潟記念（G3）',
        'distance': '2000m',
        'horses': [
            'ブレイディヴェーグ', 'シェイクユアハート', 'グランドカリナン',
            'ナムラエイハブ', 'バレエマスター', 'クイーンズウォーク',
            'ダノンベルーガ', 'サスツルギ', 'ディープモンスター',
            'シンリョクカ', 'コスモフリーゲン', 'シランケド',
            'アスクドゥポルテ', 'アスクカムオンモア', 'エネルジコ',
            'ヴェローチェエラ', 'リフレーミング'
        ]
    }
    
    result = engine.predict_race_flow_advanced(race_data)
    
    if result.get('status') == 'success':
        # ペース予測
        pace_pred = result.get('pace_prediction', {})
        print(f"\n【ペース予測】")
        print(f"予想ペース: {pace_pred.get('pace')}")
        print(f"前半3F平均: {pace_pred.get('zenhan_avg', 0):.1f}秒")
        
        # 展開適性スコアの詳細表示
        print(f"\n【改善後の展開適性スコア】")
        flow_matching = result.get('flow_matching', {})
        
        # スコアでソートして表示
        sorted_matching = sorted(flow_matching.items(), key=lambda x: x[1], reverse=True)
        
        for i, (horse, score) in enumerate(sorted_matching, 1):
            print(f"{i:2}位: {horse:15} {score:5.1f}点")
        
        # スコアの分布を分析
        scores = list(flow_matching.values())
        unique_scores = set(scores)
        
        print(f"\n【スコア分布の改善】")
        print(f"ユニークなスコア数: {len(unique_scores)}種類 （改善前: 2種類）")
        print(f"最高点: {max(scores):.1f}点")
        print(f"最低点: {min(scores):.1f}点")
        print(f"スコア範囲: {max(scores) - min(scores):.1f}点")
        
        # スコアの標準偏差を計算
        import statistics
        if len(scores) > 1:
            std_dev = statistics.stdev(scores)
            print(f"標準偏差: {std_dev:.2f}点 （差別化の指標）")
        
        print(f"\n【改善効果】")
        if len(unique_scores) > 10:
            print("✅ 成功: 各馬が細かく差別化されています！")
        elif len(unique_scores) > 5:
            print("⚠️ 部分的改善: ある程度の差別化が実現")
        else:
            print("❌ 不十分: まだ差別化が不足しています")
        
        # 上位5頭
        print(f"\n【総合上位5頭】")
        if 'race_simulation' in result and 'finish' in result['race_simulation']:
            finish_order = result['race_simulation']['finish']
            for i, horse_info in enumerate(finish_order[:5], 1):
                horse_name = horse_info.get('horse_name', '不明')
                position = horse_info.get('position', 99)
                flow_score = flow_matching.get(horse_name, 0)
                print(f"{i}位: {horse_name:15} (予測値: {position:5.2f}, 展開適性: {flow_score:5.1f}点)")

if __name__ == "__main__":
    test_improved_flow_matching()