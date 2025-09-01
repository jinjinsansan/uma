#!/usr/bin/env python3
"""
フローマッチングスコアのテスト
"""

from services.viewlogic_engine import ViewLogicEngine

def test_flow_matching():
    """フローマッチングスコアの差別化をテスト"""
    
    # エンジン初期化
    engine = ViewLogicEngine()
    
    # テストレース
    test_race = {
        'venue': '新潟',
        'race_number': 2,
        'distance': '1800m',
        'horses': ['バッキンガムパレス', 'ヴィジブルライト', 'サトノアルタイル', 'テストホースA', 'テストホースB']
    }
    
    # predict_race_flow_advancedを呼び出し
    result = engine.predict_race_flow_advanced(test_race)
    
    if result.get('status') == 'success':
        flow_matching = result.get('flow_matching', {})
        
        print("\n【フローマッチングスコア】")
        scores = []
        for horse, score in flow_matching.items():
            scores.append(score)
            print(f"{horse}: {score:.1f}点")
        
        # 統計
        print(f"\n最高点: {max(scores):.1f}")
        print(f"最低点: {min(scores):.1f}")
        print(f"点差: {max(scores) - min(scores):.1f}")
        
        # 問題の確認
        if all(s == 100.0 for s in scores):
            print("\n⚠️ 問題：全ての馬が100点です！")
        elif max(scores) - min(scores) < 10:
            print("\n⚠️ 問題：点差が小さすぎます（10点未満）")
        else:
            print("\n✅ 正常：適切な差別化ができています")
    else:
        print(f"エラー: {result.get('message', '不明')}")

if __name__ == "__main__":
    test_flow_matching()