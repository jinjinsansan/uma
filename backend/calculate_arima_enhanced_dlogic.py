#!/usr/bin/env python3
"""
2024年有馬記念出走馬の実績ベースD-Logic分析
実際のレースデータ（オッズ、人気、着順）を使用
"""
import json
import os
from typing import Dict, List, Any

def calculate_enhanced_dlogic_from_race_data():
    """実際のレースデータを使ってD-Logic計算"""
    print("🏆 2024年有馬記念 実績ベースD-Logic分析")
    print("=" * 50)
    
    # 現在の有馬記念データを取得
    import requests
    response = requests.get('http://localhost:8001/api/past-races')
    data = response.json()
    
    arima_race = None
    for race in data['races']:
        if '有馬記念' in race['raceName']:
            arima_race = race
            break
    
    if not arima_race:
        print("❌ 有馬記念データが見つかりません")
        return
    
    enhanced_horses = []
    
    for horse in arima_race['horses']:
        # 実績ベースD-Logic計算
        score = calculate_race_based_dlogic(horse)
        
        enhanced_horse = horse.copy()
        enhanced_horse['dLogicScore'] = score
        enhanced_horses.append(enhanced_horse)
        
        print(f"🐎 {horse['name']:15s} D-Logic: {score:3d} (着順: {horse.get('result', '?')}着)")
    
    # D-Logic順位を再計算
    enhanced_horses.sort(key=lambda x: x['dLogicScore'], reverse=True)
    for i, horse in enumerate(enhanced_horses):
        horse['dLogicRank'] = i + 1
    
    # 結果を保存
    output_data = {
        'race': '有馬記念',
        'year': 2024,
        'horses': enhanced_horses,
        'calculation_method': 'enhanced_race_data_based'
    }
    
    output_path = os.path.join(os.path.dirname(__file__), "data", "arima_enhanced_dlogic.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 強化版D-Logic計算完了!")
    print(f"📁 保存先: {output_path}")
    
    print(f"\n🏆 D-Logic予想順位:")
    for horse in enhanced_horses:
        result_str = f"({horse.get('result', '?')}着)" if horse.get('result') else ""
        print(f"  {horse['dLogicRank']:2d}位: {horse['name']:15s} {horse['dLogicScore']:3d} {result_str}")
    
    return enhanced_horses

def calculate_race_based_dlogic(horse_data: Dict) -> int:
    """実際のレースデータベースのD-Logic計算（強化版）"""
    base_score = 100  # ダンスインザダーク基準
    
    # 1. 人気による補正（有馬記念は超激戦）
    popularity = horse_data.get('popularity', 10)
    if popularity == 1:
        popularity_bonus = 40  # 1番人気は大幅プラス
    elif popularity <= 2:
        popularity_bonus = 30
    elif popularity <= 3:
        popularity_bonus = 20
    elif popularity <= 5:
        popularity_bonus = 10
    elif popularity <= 8:
        popularity_bonus = 0
    else:
        popularity_bonus = -15
    
    # 2. オッズによる補正（市場の評価）
    try:
        odds_str = str(horse_data.get('odds', '10.0')).replace('倍', '')
        odds = float(odds_str)
        
        if odds <= 2.0:
            odds_bonus = 35
        elif odds <= 3.0:
            odds_bonus = 25
        elif odds <= 5.0:
            odds_bonus = 15
        elif odds <= 10.0:
            odds_bonus = 5
        elif odds <= 20.0:
            odds_bonus = -5
        else:
            odds_bonus = -15
    except:
        odds_bonus = 0
    
    # 3. 実績による補正（結果が分かっている場合）
    result = horse_data.get('result')
    if result:
        if result == 1:
            result_bonus = 45  # 勝利は最高評価
        elif result == 2:
            result_bonus = 25
        elif result == 3:
            result_bonus = 15
        elif result <= 5:
            result_bonus = 5
        elif result <= 8:
            result_bonus = -5
        else:
            result_bonus = -15
    else:
        result_bonus = 0
    
    # 4. 馬体重・年齢による微調整
    age = horse_data.get('age', 4)
    if age == 3:
        age_bonus = 5  # 若い馬
    elif age <= 5:
        age_bonus = 0  # 適齢期
    else:
        age_bonus = -5  # ベテラン
    
    # 5. 性別による補正
    sex = horse_data.get('sex', '牡')
    if sex == '牝':
        sex_bonus = 3  # 牝馬は斤量軽い
    else:
        sex_bonus = 0
    
    total_score = base_score + popularity_bonus + odds_bonus + result_bonus + age_bonus + sex_bonus
    
    # G1レベルなので最低75、最高155
    final_score = max(75, min(155, total_score))
    
    return int(final_score)

if __name__ == "__main__":
    calculate_enhanced_dlogic_from_race_data()