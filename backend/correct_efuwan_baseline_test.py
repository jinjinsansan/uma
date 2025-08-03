#!/usr/bin/env python3
"""
正しいエフワンライデン基準D-Logic計算
エフワンライデンを100として、他の馬を100以下で評価
"""
import json
import os
from services.advanced_d_logic_analyzer import AdvancedDLogicAnalyzer

class EfuwanBaselineCalculator:
    """エフワンライデン基準D-Logic計算機"""
    
    def __init__(self):
        self.analyzer = AdvancedDLogicAnalyzer()
        # エフワンライデンの実際のスコア（Phase Dナレッジベースから）
        self.efuwan_actual_score = 73.63
        print(f"🎯 基準設定: エフワンライデン({self.efuwan_actual_score}点) = 100点")
    
    def calculate_efuwan_baseline_score(self, horse_name: str) -> float:
        """エフワンライデン基準でのD-Logicスコア計算"""
        
        # エフワンライデン自身の場合は100を返す
        if horse_name == "エフワンライデン":
            return 100.0
        
        # 他の馬の実際のスコアを取得
        analysis_result = self.analyzer.analyze_horse_complete_profile(horse_name)
        
        if "error" in analysis_result:
            return 50.0  # デフォルトスコア
        
        actual_score = analysis_result.get('dance_in_the_dark_total_score', 50.0)
        
        # エフワンライデン基準での相対スコア計算
        # エフワンライデンより強い馬は存在しないので、最大100に制限
        relative_score = min(100.0, (actual_score / self.efuwan_actual_score) * 100)
        
        return relative_score

def test_correct_efuwan_baseline():
    """正しいエフワンライデン基準テスト"""
    print("🏆 正しいエフワンライデン基準D-Logic計算テスト")
    print("=" * 60)
    
    calculator = EfuwanBaselineCalculator()
    
    # 2024年有馬記念16頭
    arima_horses = [
        "レガレイラ", "ダノンデサイル", "アーバンシック", "ドウデュース",
        "ベラジオオペラ", "ジャスティンパレス", "シャフリヤール", "ローシャムパーク",
        "スターズオンアース", "プログノーシス", "ブローザホーン", "ディープボンド",
        "シュトルーヴェ", "スタニングローズ", "ダノンベルーガ", "ハヤヤッコ"
    ]
    
    print(f"\n📊 エフワンライデン基準D-Logicスコア:")
    
    results = []
    for horse_name in arima_horses:
        print(f"🔍 {horse_name} 分析中...")
        
        try:
            score = calculator.calculate_efuwan_baseline_score(horse_name)
            
            # グレード判定
            if score >= 90:
                grade = "SS (伝説級)"
            elif score >= 80:
                grade = "S (超一流)"
            elif score >= 70:
                grade = "A (一流)"
            elif score >= 60:
                grade = "B (良馬)"
            elif score >= 50:
                grade = "C (平均)"
            else:
                grade = "D (要改善)"
            
            results.append({
                'name': horse_name,
                'efuwan_score': score,
                'grade': grade
            })
            
            print(f"  ✅ {horse_name:15s} {score:6.1f} - {grade}")
            
        except Exception as e:
            print(f"  ❌ {horse_name:15s} エラー: {e}")
            results.append({
                'name': horse_name,
                'efuwan_score': 50.0,
                'grade': "C (平均)"
            })
    
    # スコア順でソート
    results.sort(key=lambda x: x['efuwan_score'], reverse=True)
    
    print(f"\n🏆 エフワンライデン基準D-Logic予想順位:")
    for i, horse in enumerate(results, 1):
        print(f"  {i:2d}位: {horse['name']:15s} {horse['efuwan_score']:6.1f} - {horse['grade']}")
    
    # エフワンライデンとの比較
    print(f"\n📈 エフワンライデン(100.0)との比較:")
    for horse in results[:5]:  # 上位5頭
        diff = horse['efuwan_score'] - 100.0
        if diff > 0:
            print(f"  {horse['name']:15s} +{diff:5.1f} (エフワンライデンより強い)")
        else:
            print(f"  {horse['name']:15s} {diff:6.1f} (エフワンライデンより弱い)")
    
    # 結果保存
    output_data = {
        "baseline_horse": "エフワンライデン",
        "baseline_score": 100.0,
        "calculation_method": "efuwan_baseline_capped_at_100",
        "horses": results,
        "test_date": "2025-08-02"
    }
    
    output_path = os.path.join(os.path.dirname(__file__), "data", "correct_efuwan_baseline.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 正しいエフワンライデン基準テスト完了!")
    print(f"📁 結果保存: {output_path}")
    
    return results

if __name__ == "__main__":
    test_correct_efuwan_baseline()