#!/usr/bin/env python3
"""
有馬記念のD-Logicスコアを正確な値に更新
"""
import json
import os

def update_arima_dlogic_scores():
    """有馬記念の簡易スコアを正確なスコアに差し替え"""
    
    # 強化版D-Logicスコアを読み込み
    enhanced_path = os.path.join(os.path.dirname(__file__), "data", "arima_enhanced_dlogic.json")
    with open(enhanced_path, 'r', encoding='utf-8') as f:
        enhanced_data = json.load(f)
    
    # 元の2024年G1レースデータを読み込み
    original_path = os.path.join(os.path.dirname(__file__), "data", "2024_real_g1_races.json")
    with open(original_path, 'r', encoding='utf-8') as f:
        original_data = json.load(f)
    
    # 有馬記念レースを検索
    arima_race = None
    arima_index = None
    for i, race in enumerate(original_data['races']):
        if '有馬記念' in race['raceName']:
            arima_race = race
            arima_index = i
            break
    
    if not arima_race:
        print("❌ 有馬記念が見つかりません")
        return
    
    print("🔄 有馬記念D-Logicスコア更新中...")
    
    # 強化版スコアで馬データを更新
    enhanced_horses = enhanced_data['horses']
    
    # 馬名をキーとした辞書作成
    enhanced_scores = {}
    for horse in enhanced_horses:
        enhanced_scores[horse['name']] = {
            'dLogicScore': horse['dLogicScore'],
            'dLogicRank': horse['dLogicRank']
        }
    
    # 元データの馬情報を更新
    updated_horses = []
    for horse in arima_race['horses']:
        horse_name = horse['name']
        if horse_name in enhanced_scores:
            # D-Logicスコアと順位を更新
            horse['dLogicScore'] = enhanced_scores[horse_name]['dLogicScore']
            horse['dLogicRank'] = enhanced_scores[horse_name]['dLogicRank']
            
            # 勝率予想を再計算
            score = horse['dLogicScore']
            if score >= 140:
                win_prob = round(85 + (score - 140) * 0.3, 1)
            elif score >= 120:
                win_prob = round(65 + (score - 120) * 1.0, 1)
            elif score >= 100:
                win_prob = round(35 + (score - 100) * 1.5, 1)
            else:
                win_prob = round(10 + (score - 80) * 1.25, 1)
            
            horse['winProbability'] = min(95.0, win_prob)
            
            print(f"  ✅ {horse_name:15s} D-Logic: {horse['dLogicScore']:3d} (順位: {horse['dLogicRank']:2d}位)")
        
        updated_horses.append(horse)
    
    # 更新されたデータを元に戻す
    original_data['races'][arima_index]['horses'] = updated_horses
    original_data['races'][arima_index]['description'] = "2024年有馬記念（16頭立て）- 正確なD-Logic分析"
    
    # ファイルに保存
    with open(original_path, 'w', encoding='utf-8') as f:
        json.dump(original_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n🎯 有馬記念D-Logicスコア更新完了!")
    print(f"📁 更新ファイル: {original_path}")
    print("\n🏆 最終D-Logic予想:")
    
    # D-Logic順で表示
    sorted_horses = sorted(updated_horses, key=lambda x: x['dLogicScore'], reverse=True)
    for horse in sorted_horses:
        result_str = f"→ {horse.get('result', '?')}着" if horse.get('result') else ""
        print(f"  {horse['dLogicRank']:2d}位: {horse['name']:15s} {horse['dLogicScore']:3d} {result_str}")

if __name__ == "__main__":
    update_arima_dlogic_scores()