#!/usr/bin/env python3
"""
エフワンライデン基準D-Logic再計算テスト
エフワンライデン(73.63点)を100として有馬記念16頭を相対評価
"""
import json
import os

def efuwan_baseline_test():
    """エフワンライデン基準D-Logic計算テスト"""
    print("🏆 エフワンライデン基準D-Logic再計算テスト")
    print("=" * 50)
    
    # エフワンライデンのPhase Dナレッジベースからのスコア
    efuwan_score = 73.63
    print(f"🎯 基準馬: エフワンライデン - {efuwan_score}点を100として設定")
    
    # 2024年有馬記念16頭の実際のD-Logicスコア（先ほどの結果）
    arima_horses = [
        {"name": "ドウデュース", "score": 92},
        {"name": "ダノンデサイル", "score": 75},
        {"name": "シャフリヤール", "score": 72},
        {"name": "スタニングローズ", "score": 71},
        {"name": "ベラジオオペラ", "score": 70},
        {"name": "アーバンシック", "score": 65},
        {"name": "ハヤヤッコ", "score": 64},
        {"name": "レガレイラ", "score": 62},
        {"name": "ジャスティンパレス", "score": 62},
        {"name": "プログノーシス", "score": 54},
        {"name": "ディープボンド", "score": 45},
        {"name": "シュトルーヴェ", "score": 41},
        {"name": "ローシャムパーク", "score": 39},
        {"name": "ブローザホーン", "score": 34},
        {"name": "ダノンベルーガ", "score": 28},
        {"name": "スターズオンアース", "score": 25}
    ]
    
    print(f"\n🔄 エフワンライデン基準での相対計算:")
    print(f"📐 変換式: (馬のスコア / {efuwan_score}) × 100")
    
    recalculated_horses = []
    
    for horse in arima_horses:
        # エフワンライデンを100とした相対スコア
        relative_score = (horse['score'] / efuwan_score) * 100
        
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
            'original_score': horse['score'],
            'relative_score': relative_score,
            'new_grade': new_grade
        })
        
        print(f"  🐎 {horse['name']:15s} {horse['score']:3d} → {relative_score:6.1f} - {new_grade}")
    
    print(f"\n🏆 エフワンライデン基準D-Logic予想順位:")
    for i, horse in enumerate(recalculated_horses, 1):
        print(f"  {i:2d}位: {horse['name']:15s} {horse['relative_score']:6.1f} - {horse['new_grade']}")
    
    # 比較分析
    print(f"\n📊 スコア分析:")
    print(f"  最高スコア: {recalculated_horses[0]['name']} - {recalculated_horses[0]['relative_score']:.1f}")
    print(f"  最低スコア: {recalculated_horses[-1]['name']} - {recalculated_horses[-1]['relative_score']:.1f}")
    
    # 100点超えの馬（エフワンライデンより強い馬）
    stronger_horses = [h for h in recalculated_horses if h['relative_score'] > 100]
    if stronger_horses:
        print(f"\n⭐ エフワンライデンより強い馬:")
        for horse in stronger_horses:
            print(f"    {horse['name']:15s} {horse['relative_score']:6.1f} - {horse['new_grade']}")
    else:
        print(f"\n✅ エフワンライデンが最強（100点基準として適切）")
    
    # 結果保存
    comparison_data = {
        "baseline_horse": "エフワンライデン",
        "baseline_original_score": efuwan_score,
        "conversion_method": "strongest_horse_baseline_100",
        "horses": recalculated_horses,
        "analysis_date": "2025-08-02"
    }
    
    output_path = os.path.join(os.path.dirname(__file__), "data", "efuwan_baseline_test.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(comparison_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ エフワンライデン基準テスト完了!")
    print(f"📁 結果保存: {output_path}")
    
    return recalculated_horses

if __name__ == "__main__":
    efuwan_baseline_test()