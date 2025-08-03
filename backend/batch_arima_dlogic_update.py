#!/usr/bin/env python3
"""
2024年有馬記念16頭の12項目D-Logic一括更新
"""
import json
import os
from services.advanced_d_logic_analyzer import AdvancedDLogicAnalyzer

def batch_update_arima_dlogic():
    """有馬記念16頭の12項目D-Logic一括更新"""
    print("🏆 2024年有馬記念 12項目D-Logic一括更新開始")
    
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
    
    print(f"🎯 対象: {arima_race['raceName']} ({len(arima_race['horses'])}頭)")
    
    analyzer = AdvancedDLogicAnalyzer()
    
    # 各馬のD-Logic分析
    print("\n📊 12項目D-Logic分析結果:")
    for horse in arima_race['horses']:
        horse_name = horse['name']
        
        try:
            analysis_result = analyzer.analyze_horse_complete_profile(horse_name)
            
            if "error" not in analysis_result:
                score = analysis_result.get('dance_in_the_dark_total_score', 100)
                grade = analysis_result.get('performance_grade', 'C (平均)')
                
                # スコア更新
                horse['dLogicScore'] = int(score)
                horse['d_logic_analysis'] = analysis_result
                
                print(f"  🐎 {horse_name:15s} D-Logic: {int(score):3d} - {grade}")
                
            else:
                print(f"  ❌ {horse_name:15s} データなし - ダンスインザダーク基準100点")
                horse['dLogicScore'] = 100
                horse['d_logic_analysis'] = {'error': analysis_result.get('error')}
                
        except Exception as e:
            print(f"  ❌ {horse_name:15s} エラー: {e}")
            horse['dLogicScore'] = 100
            horse['d_logic_analysis'] = {'error': str(e)}
    
    # D-Logic順でソート
    arima_race['horses'].sort(key=lambda x: x['dLogicScore'], reverse=True)
    
    # 順位と勝率更新
    for i, horse in enumerate(arima_race['horses']):
        horse['dLogicRank'] = i + 1
        
        # ダンスインザダーク基準勝率計算
        score = horse['dLogicScore']
        if score >= 90:
            win_prob = min(95.0, 75 + (score - 90) * 1.0)
        elif score >= 80:
            win_prob = min(75.0, 55 + (score - 80) * 2.0)
        elif score >= 70:
            win_prob = min(55.0, 35 + (score - 70) * 2.0)
        elif score >= 60:
            win_prob = min(35.0, 20 + (score - 60) * 1.5)
        else:
            win_prob = max(5.0, (score - 50) * 0.5)
        
        horse['winProbability'] = round(win_prob, 1)
    
    # データ更新
    data['races'][arima_index] = arima_race
    data['races'][arima_index]['description'] = "2024年有馬記念（16頭立て）- 12項目D-Logic正確分析"
    
    # ファイル保存
    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n🏆 12項目D-Logic最終予想順位:")
    for horse in arima_race['horses']:
        result_str = f"→ {horse.get('result', '?')}着" if horse.get('result') else ""
        print(f"  {horse['dLogicRank']:2d}位: {horse['name']:15s} {horse['dLogicScore']:3d} {result_str}")
    
    print(f"\n✅ 有馬記念12項目D-Logic一括更新完了!")
    print(f"📁 更新ファイル: {data_path}")

if __name__ == "__main__":
    batch_update_arima_dlogic()