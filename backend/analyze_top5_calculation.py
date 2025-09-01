#!/usr/bin/env python3
"""
ViewLogic展開予想の上位5頭計算ロジックを分析
"""

from services.viewlogic_engine import ViewLogicEngine

def analyze_top5_calculation():
    """上位5頭の計算ロジックを分析"""
    
    print("=== ViewLogic展開予想 上位5頭の計算方法 ===\n")
    
    print("【現在の計算フロー】\n")
    
    print("1. レースシミュレーション（_simulate_race_positions）")
    print("   ├─ 各馬の過去のコーナー通過順位を取得")
    print("   ├─ 1コーナー、3コーナー、4コーナーの平均順位を計算")
    print("   └─ 最終的な着順予測へ")
    print()
    
    print("2. 着順予測（_predict_finish_position）")
    print("   ├─ 基本点 = 過去レースの着順の平均")
    print("   │   例: 過去5走が[3着,5着,2着,7着,4着] → 平均4.2着")
    print("   ├─ ペース補正")
    print("   │   ├─ ハイペース時：")
    print("   │   │   └─ 差し・追込馬 → -1.5着（有利）")
    print("   │   └─ スローペース時：")
    print("   │       └─ 逃げ・先行馬 → -1.5着（有利）")
    print("   └─ 最終予測着順 = max(1.0, 補正後の着順)")
    print()
    
    print("3. 上位5頭の選出")
    print("   └─ 予測着順でソート → 上位5頭を取得")
    print()
    
    print("【問題点】")
    print("❌ 過去の着順平均だけでは正確な予測が困難")
    print("❌ ペース補正が固定値（-1.5着）で単純すぎる")
    print("❌ フローマッチングスコアが活用されていない")
    print()
    
    print("【実際の計算例】")
    print("馬A: 過去平均3.0着 + ハイペース差し馬補正-1.5 = 1.5着")
    print("馬B: 過去平均4.0着 + 補正なし = 4.0着")
    print("馬C: 過去平均2.5着 + 補正なし = 2.5着")
    print("馬D: 過去平均5.0着 + ハイペース差し馬補正-1.5 = 3.5着")
    print("馬E: 過去平均6.0着 + 補正なし = 6.0着")
    print()
    print("→ 上位5頭: 馬A(1.5着), 馬C(2.5着), 馬D(3.5着), 馬B(4.0着), 馬E(6.0着)")
    print()
    
    # 実際のレースでテスト
    engine = ViewLogicEngine()
    test_race = {
        'venue': '新潟',
        'race_number': 2,
        'horses': ['バッキンガムパレス', 'ヴィジブルライト', 'サトノアルタイル']
    }
    
    result = engine.predict_race_flow_advanced(test_race)
    
    if result.get('status') == 'success' and 'race_simulation' in result:
        simulation = result['race_simulation']
        if 'finish' in simulation:
            print("【実際の予測結果】")
            for i, horse_info in enumerate(simulation['finish'][:5], 1):
                horse_name = horse_info.get('horse_name', '不明')
                position = horse_info.get('position', 99)
                print(f"{i}位予測: {horse_name} (予測値: {position:.1f})")

if __name__ == "__main__":
    analyze_top5_calculation()