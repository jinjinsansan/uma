#!/usr/bin/env python3
"""
9/13阪神のレースデータを更新するスクリプト
レース名、人気、オッズをMySQLから取得して追加
"""

import mysql.connector
from datetime import datetime
import json

def get_race_details():
    """MySQLから9/13阪神のレース詳細情報を取得"""
    
    conn = mysql.connector.connect(
        host="172.25.160.1",
        port=3306,
        database="mykeibadb",
        user="root",
        password="04050405Aoi-"
    )
    
    cur = conn.cursor()
    
    # 9/13阪神のレース名を取得
    query_races = """
    SELECT 
        race_number,
        racemei_hondai,
        racemei_fukudai,
        ryakusho_3
    FROM jvd_ra
    WHERE kaisai_date = '2025-09-13'
    AND jyocode = '09'
    ORDER BY race_number
    """
    
    cur.execute(query_races)
    races = cur.fetchall()
    
    race_names = {}
    for race_number, hondai, fukudai, ryakusho in races:
        # レース名の優先順位: 本題 > 副題 > 略称3
        if hondai and hondai.strip():
            race_name = hondai.strip()
        elif fukudai and fukudai.strip():
            race_name = fukudai.strip()
        elif ryakusho and ryakusho.strip():
            race_name = ryakusho.strip()
        else:
            # 3歳未勝利などの条件レース名を判定
            race_name = ""
            
        race_names[race_number] = race_name
        print(f"{race_number}R: {race_name if race_name else '(条件戦)'}")
    
    # 各レースのオッズと人気を取得
    query_odds = """
    SELECT 
        se.race_number,
        se.bamei,
        se.tansho_odds,
        se.tansho_ninkijun
    FROM jvd_se se
    WHERE se.kaisai_date = '2025-09-13'
    AND se.jyocode = '09'
    AND se.race_number IN (4, 7, 8, 9, 10, 11, 12)
    ORDER BY se.race_number, se.umaban
    """
    
    cur.execute(query_odds)
    odds_data = cur.fetchall()
    
    # レース番号ごとにデータを整理
    races_odds = {}
    for race_number, bamei, odds, ninki in odds_data:
        if race_number not in races_odds:
            races_odds[race_number] = {
                'horses': [],
                'odds': [],
                'popularities': []
            }
        races_odds[race_number]['horses'].append(bamei.strip() if bamei else '')
        races_odds[race_number]['odds'].append(float(odds) if odds else 0.0)
        races_odds[race_number]['popularities'].append(int(ninki) if ninki else 0)
    
    cur.close()
    conn.close()
    
    return race_names, races_odds

def update_hanshin_file():
    """阪神のレースファイルを更新"""
    
    race_names, races_odds = get_race_details()
    
    # 既存のファイルを読み込み
    file_path = '/mnt/e/dev/Cusor/front/d-logic-ai-frontend/src/data/archive/races-20250913-阪神.ts'
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 各レースを更新
    for race_num in [4, 7, 8, 9, 10, 11, 12]:
        if race_num in race_names:
            # レース名を更新
            old_pattern = f'race_number: {race_num},\n    race_name: \'\','
            new_pattern = f'race_number: {race_num},\n    race_name: \'{race_names[race_num]}\','
            content = content.replace(old_pattern, new_pattern)
            
            # 空文字の場合の対応
            old_pattern2 = f'race_number: {race_num},\n    race_name: "",'
            new_pattern2 = f'race_number: {race_num},\n    race_name: "{race_names[race_num]}",'
            content = content.replace(old_pattern2, new_pattern2)
        
        if race_num in races_odds:
            # オッズと人気データを更新
            data = races_odds[race_num]
            
            # レースのセクションを探して更新
            import re
            
            # このレースのセクションを探す
            pattern = rf'race_id: \'20250913-阪神-{race_num}\',[^{{]*?odds: \[[^\]]*?\],[^{{]*?popularities: \[[^\]]*?\]'
            
            def replacer(match):
                text = match.group(0)
                # オッズを更新
                text = re.sub(
                    r'odds: \[[^\]]*?\]',
                    f'odds: [{", ".join(str(o) for o in data["odds"])}]',
                    text
                )
                # 人気を更新
                text = re.sub(
                    r'popularities: \[[^\]]*?\]',
                    f'popularities: [{", ".join(str(p) for p in data["popularities"])}]',
                    text
                )
                return text
            
            content = re.sub(pattern, replacer, content, flags=re.DOTALL)
    
    # ファイルを書き戻す
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"\n✅ ファイル更新完了: {file_path}")

if __name__ == "__main__":
    print("9/13阪神のレース情報を更新中...")
    update_hanshin_file()