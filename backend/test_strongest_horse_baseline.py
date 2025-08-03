#!/usr/bin/env python3
"""
最強馬基準でのD-Logic再計算テスト
エフワンライデンを100として有馬記念16頭を相対評価
"""
import json
import os
from services.advanced_d_logic_analyzer import AdvancedDLogicAnalyzer

def test_strongest_horse_baseline():
    """最強馬基準D-Logic計算テスト"""
    print("🏆 最強馬基準D-Logic計算テスト開始")
    print("=" * 50)
    
    analyzer = AdvancedDLogicAnalyzer()
    
    # 1. エフワンライデンの実際のスコアを取得
    print("🔍 エフワンライデン（最強馬）のD-Logic分析中...")
    strongest_result = analyzer.analyze_horse_complete_profile("エフワンライデン")
    
    if "error" in strongest_result:
        print(f"❌ エフワンライデンデータ取得エラー: {strongest_result['error']}")
        return
    
    strongest_score = strongest_result.get('dance_in_the_dark_total_score', 100)
    print(f"✅ エフワンライデン実際スコア: {strongest_score:.1f}")
    
    # 2. 有馬記念16頭のスコア取得
    arima_horses = [
        "レガレイラ", "ダノンデサイル", "アーバンシック", "ドウデュース",
        "ベラジオオペラ", "ジャスティンパレス", "シャフリヤール", "ローシャムパーク",
        "スターズオンアース", "プログノーシス", "ブローザホーン", "ディープボンド",
        "シュトルーヴェ", "スタニングローズ", "ダノンベルーガ", "ハヤヤッコ"
    ]
    
    print(f"\n📊 有馬記念16頭の実際D-Logicスコア:")
    horse_scores = []
    
    for horse_name in arima_horses:
        analysis_result = analyzer.analyze_horse_complete_profile(horse_name)
        
        if "error" not in analysis_result:
            score = analysis_result.get('dance_in_the_dark_total_score', 100)
            grade = analysis_result.get('performance_grade', 'C (平均)')
            horse_scores.append({
                'name': horse_name,
                'original_score': score,
                'grade': grade
            })
            print(f"  🐎 {horse_name:15s} {score:6.1f} - {grade}")
        else:
            horse_scores.append({
                'name': horse_name,
                'original_score': 100,
                'grade': 'C (平均)'
            })
            print(f"  ❌ {horse_name:15s} データなし")
    
    # 3. エフワンライデン基準100で再計算
    print(f"\n🔄 エフワンライデン基準100での相対計算:")
    print(f"📐 変換式: (馬のスコア / {strongest_score:.1f}) × 100")
    
    recalculated_horses = []
    for horse in horse_scores:
        # エフワンライデンを100とした相対スコア
        relative_score = (horse['original_score'] / strongest_score) * 100
        
        # 新しいグレード判定
        if relative_score >= 90:
            new_grade = "SS (伝説級)"
        elif relative_score >= 80:
            new_grade = "S (超一流)"
        elif relative_score >= 70:
            new_grade = "A (一流)"
        elif relative_score >= 60:
            new_grade = "B (良馬)"
        elif relative_score >= 50:
            new_grade = "C (平均)"
        else:
            new_grade = "D (要改善)"
        
        recalculated_horses.append({
            'name': horse['name'],
            'original_score': horse['original_score'],
            'relative_score': relative_score,
            'new_grade': new_grade
        })
        
        print(f"  🐎 {horse['name']:15s} {horse['original_score']:6.1f} → {relative_score:6.1f} - {new_grade}")
    
    # 4. 相対スコア順でソート
    recalculated_horses.sort(key=lambda x: x['relative_score'], reverse=True)
    
    print(f"\n🏆 エフワンライデン基準D-Logic予想順位:")
    for i, horse in enumerate(recalculated_horses, 1):
        print(f"  {i:2d}位: {horse['name']:15s} {horse['relative_score']:6.1f} - {horse['new_grade']}")
    
    # 5. 比較結果保存
    comparison_data = {
        "baseline_horse": "エフワンライデン",
        "baseline_score": strongest_score,
        "conversion_factor": strongest_score / 100,
        "horses": recalculated_horses,
        "calculation_method": "strongest_horse_baseline"
    }
    
    output_path = os.path.join(os.path.dirname(__file__), "data", "strongest_horse_baseline_test.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(comparison_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 最強馬基準テスト完了!")
    print(f"📁 結果保存: {output_path}")
    
    return recalculated_horses

if __name__ == "__main__":
    test_strongest_horse_baseline()