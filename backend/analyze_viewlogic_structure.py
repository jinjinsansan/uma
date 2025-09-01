#!/usr/bin/env python3
"""
ViewLogicEngineの構造を分析
"""

import re

def analyze_viewlogic():
    """ViewLogicEngineの構造を分析"""
    
    with open('services/viewlogic_engine.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 主要な関数を抽出
    functions = re.findall(r'def ((?:_)?(?:advanced_|calculate_|classify_|simulate_)[a-z_]+)\(', content)
    
    print("=== ViewLogic展開予想の主要関数 ===\n")
    
    # predict_race_flow_advancedの流れ
    print("【メイン関数】")
    print("predict_race_flow_advanced()")
    print("  ├─ 1. _advanced_pace_prediction() - ペース予測")
    print("  ├─ 2. _classify_detailed_styles() - 脚質分類")  
    print("  ├─ 3. _calculate_position_stability_all() - 位置取り安定性")
    print("  ├─ 4. _calculate_flow_matching() - 展開適性マッチング ← 問題箇所")
    print("  └─ 5. _simulate_race_positions() - 展開シミュレーション")
    
    print("\n【各関数の役割】")
    
    # 各関数の概要を抽出
    for func in ['_advanced_pace_prediction', '_calculate_flow_matching', '_calculate_style_index']:
        pattern = rf'def {func}\([^)]*\)[^:]*:\s*"""([^"]*?)"""'
        match = re.search(pattern, content, re.DOTALL)
        if match:
            print(f"\n{func}:")
            print(f"  {match.group(1).strip()}")
    
    # _calculate_flow_matchingの詳細を確認
    print("\n【_calculate_flow_matchingの現在の処理】")
    pattern = r'def _calculate_flow_matching\(.*?\).*?:\s*""".*?"""(.*?)(?=\n    def |\Z)'
    match = re.search(pattern, content, re.DOTALL)
    if match:
        lines = match.group(1).strip().split('\n')
        for line in lines[:30]:  # 最初の30行
            if 'if' in line or 'else' in line or 'score' in line:
                print(line.strip())

if __name__ == "__main__":
    analyze_viewlogic()