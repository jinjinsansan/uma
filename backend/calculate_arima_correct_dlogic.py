#!/usr/bin/env python3
"""
2024年有馬記念出走馬16頭の正確な12項目D-Logic分析
advanced_d_logic_analyzer.pyを使用
"""
import json
import os
from services.advanced_d_logic_analyzer import AdvancedDLogicAnalyzer

# 2024年有馬記念出走馬16頭
ARIMA_HORSES = [
    "レガレイラ",
    "ダノンデサイル", 
    "アーバンシック",
    "ドウデュース",
    "ベラジオオペラ",
    "ローシャムパーク",
    "スターズオンアース",
    "レガレイラ",
    "ディープボンド",
    "プログノーシス",
    "ジャスティンパレス",
    "シュトルーヴェ",
    "スタニングローズ",
    "ダノンベルーガ",
    "ハヤヤッコ",
    "シャフリヤール"
]

def calculate_correct_arima_dlogic():
    """有馬記念出走馬の正確な12項目D-Logic分析"""
    print("🏆 2024年有馬記念 正確な12項目D-Logic分析開始")
    print("=" * 60)
    
    analyzer = AdvancedDLogicAnalyzer()
    results = []
    
    for i, horse_name in enumerate(ARIMA_HORSES, 1):
        print(f"\n🐎 {i:2d}/16 {horse_name} 12項目D-Logic分析中...")
        
        # 正確な12項目D-Logic分析実行
        analysis_result = analyzer.analyze_horse_complete_profile(horse_name)
        
        if "error" not in analysis_result:
            score = analysis_result.get('dance_in_the_dark_total_score', 100)
            grade = analysis_result.get('performance_grade', 'C (平均)')
            print(f"  ✅ D-Logic Score: {score:.1f} - {grade}")
            
            results.append({
                'name': horse_name,
                'dLogicScore': int(score),
                'analysis': analysis_result
            })
        else:
            print(f"  ❌ エラー: {analysis_result.get('error')}")
            # エラー時はダンスインザダーク基準スコア
            results.append({
                'name': horse_name,
                'dLogicScore': 100,
                'analysis': {'error': analysis_result.get('error')}
            })
    
    # D-Logic順位でソート
    results.sort(key=lambda x: x['dLogicScore'], reverse=True)
    
    # 順位付け
    for i, horse in enumerate(results):
        horse['dLogicRank'] = i + 1
    
    print(f"\n🏆 正確な12項目D-Logic予想順位:")
    for horse in results:
        print(f"  {horse['dLogicRank']:2d}位: {horse['name']:15s} {horse['dLogicScore']:3d}")
    
    # 結果を保存
    output_data = {
        'race': '有馬記念',
        'year': 2024,
        'date': '2024-12-22',
        'horses': results,
        'total_horses': len(results),
        'analysis_method': '12項目D-Logic分析システム',
        'baseline': 'ダンスインザダーク基準100点'
    }
    
    output_path = os.path.join(os.path.dirname(__file__), "data", "arima_correct_dlogic.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 正確な12項目D-Logic分析完了!")
    print(f"📁 保存先: {output_path}")
    
    return results

if __name__ == "__main__":
    calculate_correct_arima_dlogic()