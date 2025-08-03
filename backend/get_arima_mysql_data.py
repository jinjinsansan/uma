#!/usr/bin/env python3
"""
MySQLから2024年有馬記念の実際の馬データを取得してD-Logic計算
"""
import mysql.connector
import json
import os
from typing import Dict, List, Any
from services.integrated_d_logic_calculator import IntegratedDLogicCalculator

def get_mysql_connection():
    """MySQL接続を取得"""
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='mykeibadb',
        charset='utf8mb4'
    )

def get_arima_kinen_2024_data():
    """MySQLから2024年有馬記念の実際のデータを取得"""
    print("🏆 MySQLから2024年有馬記念データ取得中...")
    
    conn = get_mysql_connection()
    cursor = conn.cursor(dictionary=True)
    
    # 2024年有馬記念を検索
    race_query = """
    SELECT DISTINCT
        RACE_CODE,
        KAISAI_DATE,
        KEIBAJO_CODE,
        RACE_BANGO,
        KYOSOMEI_HONDAI
    FROM umagoto_race_joho 
    WHERE KAISAI_DATE LIKE '2024%' 
    AND KYOSOMEI_HONDAI LIKE '%有馬記念%'
    LIMIT 5
    """
    
    cursor.execute(race_query)
    races = cursor.fetchall()
    
    print(f"📊 検索結果: {len(races)}件のレース")
    for race in races:
        print(f"  📅 {race['KAISAI_DATE']} {race['KYOSOMEI_HONDAI']}")
    
    if not races:
        print("❌ 2024年有馬記念が見つかりません")
        return None
    
    # 最初のレースを使用
    target_race = races[0]
    race_code = target_race['RACE_CODE']
    
    print(f"🎯 対象レース: {target_race['KYOSOMEI_HONDAI']} (コード: {race_code})")
    
    # 出走馬データを取得
    horse_query = """
    SELECT 
        UMABAN,
        BAMEI,
        KISHU_RYAKUSHO,
        CHOKYOSHI_RYAKUSHO,
        FUTAN_JURYO,
        BATAIJU,
        ZOGEN_SA,
        BAREI,
        SEI_BETU,
        TANSHO_ODDS,
        TANSHO_NINKI,
        CHAKUJUN,
        SHUSSO_TOSU
    FROM umagoto_race_joho 
    WHERE RACE_CODE = %s
    ORDER BY CAST(UMABAN AS UNSIGNED)
    """
    
    cursor.execute(horse_query, (race_code,))
    horses = cursor.fetchall()
    
    print(f"🐎 出走馬数: {len(horses)}頭")
    
    cursor.close()
    conn.close()
    
    return {
        'race_info': target_race,
        'horses': horses
    }

def calculate_dlogic_from_mysql_data():
    """MySQLデータを使ってD-Logic計算"""
    mysql_data = get_arima_kinen_2024_data()
    if not mysql_data:
        return
    
    print("\n🚀 D-Logic計算開始...")
    calculator = IntegratedDLogicCalculator()
    results = []
    
    for horse in mysql_data['horses']:
        horse_name = horse['BAMEI']
        print(f"\n🐎 {horse_name} を分析中...")
        
        # MySQLの実際のデータを使ってD-Logic計算
        horse_data = {
            'horse_name': horse_name,
            'number': horse.get('UMABAN'),
            'jockey': horse.get('KISHU_RYAKUSHO'),
            'trainer': horse.get('CHOKYOSHI_RYAKUSHO'),
            'weight': horse.get('FUTAN_JURYO'),
            'horse_weight': horse.get('BATAIJU'),
            'weight_change': horse.get('ZOGEN_SA'),
            'age': horse.get('BAREI'),
            'sex': horse.get('SEI_BETU'),
            'odds': horse.get('TANSHO_ODDS'),
            'popularity': horse.get('TANSHO_NINKI'),
            'result': horse.get('CHAKUJUN'),
            'entry_count': horse.get('SHUSSO_TOSU'),
            'analysis_type': 'comprehensive'
        }
        
        # D-Logic分析実行
        analysis_result = calculator.calculate_d_logic_score(horse_data)
        
        score = analysis_result.get('total_score', 100)
        print(f"  ✅ D-Logic Score: {score:.1f}")
        
        results.append({
            'name': horse_name,
            'mysql_data': horse_data,
            'dLogicScore': int(score),
            'analysis': analysis_result
        })
    
    # 結果をソート
    results.sort(key=lambda x: x['dLogicScore'], reverse=True)
    
    # 順位付け
    for i, horse in enumerate(results):
        horse['dLogicRank'] = i + 1
    
    print(f"\n🏆 MySQL実データD-Logic予想:")
    for horse in results:
        result_str = f"({horse['mysql_data'].get('result', '?')}着)" if horse['mysql_data'].get('result') else ""
        print(f"  {horse['dLogicRank']:2d}位: {horse['name']:15s} {horse['dLogicScore']:3d} {result_str}")
    
    # 結果を保存
    output_data = {
        'race': '有馬記念',
        'year': 2024,
        'source': 'MySQL mykeibadb',
        'horses': results,
        'race_info': mysql_data['race_info']
    }
    
    output_path = os.path.join(os.path.dirname(__file__), "data", "arima_mysql_dlogic.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ MySQL実データD-Logic分析完了!")
    print(f"📁 保存先: {output_path}")
    
    return results

if __name__ == "__main__":
    calculate_dlogic_from_mysql_data()