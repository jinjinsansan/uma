#!/usr/bin/env python3
"""
2024年有馬記念の正確な12項目D-Logicスコアで更新
"""
import json
import os
from services.advanced_d_logic_analyzer import AdvancedDLogicAnalyzer

def update_arima_with_correct_dlogic():
    """有馬記念の12項目D-Logicスコアで更新"""
    print("🏆 2024年有馬記念 12項目D-Logic正確計算開始")
    print("=" * 50)
    
    # 既存データ読み込み
    data_path = os.path.join(os.path.dirname(__file__), "data", "2024_real_g1_races.json")
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 有馬記念を検索
    arima_race = None
    arima_index = None
    for i, race in enumerate(data['races']):
        if '有馬記念' in race['raceName']:
            arima_race = race
            arima_index = i
            break
    
    if not arima_race:
        print("❌ 有馬記念が見つかりません")
        return
    
    print(f"🎯 対象レース: {arima_race['raceName']} ({len(arima_race['horses'])}頭)")
    
    analyzer = AdvancedDLogicAnalyzer()
    updated_horses = []
    
    for horse in arima_race['horses']:
        horse_name = horse['name']
        print(f"\n🐎 {horse_name} 12項目D-Logic分析中...")
        
        # 12項目D-Logic分析実行
        analysis_result = analyzer.analyze_horse_complete_profile(horse_name)
        
        if "error" not in analysis_result:
            score = analysis_result.get('dance_in_the_dark_total_score', 100)
            grade = analysis_result.get('performance_grade', 'C (平均)')
            print(f"  ✅ D-Logic Score: {score:.1f} - {grade}")
            
            # スコア更新
            horse['dLogicScore'] = int(score)
            horse['d_logic_analysis'] = analysis_result
            
        else:
            print(f"  ❌ データなし: ダンスインザダーク基準100点")
            horse['dLogicScore'] = 100  # ダンスインザダーク基準
            horse['d_logic_analysis'] = {'error': analysis_result.get('error')}
        
        updated_horses.append(horse)
    
    # D-Logic順でソート
    updated_horses.sort(key=lambda x: x['dLogicScore'], reverse=True)
    
    # 順位更新
    for i, horse in enumerate(updated_horses):
        horse['dLogicRank'] = i + 1
        
        # 勝率再計算
        score = horse['dLogicScore']
        if score >= 90:
            win_prob = min(95.0, 80 + (score - 90) * 0.5)
        elif score >= 80:
            win_prob = min(80.0, 60 + (score - 80) * 2.0)
        elif score >= 70:
            win_prob = min(60.0, 40 + (score - 70) * 2.0)
        else:
            win_prob = max(5.0, (score - 50) * 0.8)
        
        horse['winProbability'] = round(win_prob, 1)
    
    # データ更新
    data['races'][arima_index]['horses'] = updated_horses
    data['races'][arima_index]['description'] = "2024年有馬記念（16頭立て）- 正確な12項目D-Logic分析"
    
    # ファイル保存
    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n🏆 正確な12項目D-Logic予想順位:")
    for horse in updated_horses:
        result_str = f"→ {horse.get('result', '?')}着" if horse.get('result') else ""
        print(f"  {horse['dLogicRank']:2d}位: {horse['name']:15s} {horse['dLogicScore']:3d} {result_str}")
    
    print(f"\n✅ 有馬記念D-Logic正確スコア更新完了!")
    print(f"📁 更新ファイル: {data_path}")

if __name__ == "__main__":
    update_arima_with_correct_dlogic()