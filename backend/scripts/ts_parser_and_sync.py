#!/usr/bin/env python3
"""
TSファイルをパースしてSupabaseに同期する実装版
実際のTSファイル構造に対応
"""

import os
import re
import json
import glob
from datetime import datetime
from typing import Dict, List, Any, Optional
import subprocess

# Supabase設定はここに実際の値を入れてください
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_ANON_KEY = "your-anon-key"

def parse_ts_file(filepath: str) -> Optional[Dict[str, Any]]:
    """TSファイルをパースしてレース情報を抽出"""
    
    # ファイル名から日付と会場を抽出
    filename = os.path.basename(filepath)
    match = re.match(r'races-(\d{8})-(.+)\.ts', filename)
    if not match:
        print(f"ファイル名が想定外: {filename}")
        return None
    
    date_str = match.group(1)
    venue = match.group(2)
    
    # 日付をYYYY-MM-DD形式に変換
    date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # レースデータを抽出
    races = []
    
    # 各レースブロックを抽出（正規表現パターン）
    race_pattern = r'\{[^}]*race_id:[^}]*?\}(?:\s*,)?'
    
    # より詳細なパターンでレース情報を抽出
    detailed_pattern = r'''
        \{
        \s*race_id:\s*"([^"]+)",?\s*
        (?:race_date:\s*"([^"]+)",?\s*)?
        (?:venue:\s*"([^"]+)",?\s*)?
        (?:race_number:\s*(\d+),?\s*)?
        (?:race_name:\s*"([^"]*)",?\s*)?
        (?:horses:\s*\[([^\]]*)\],?\s*)?
        (?:distance:\s*"([^"]*)",?\s*)?
        (?:track_condition:\s*"([^"]*)",?\s*)?
        (?:jockeys:\s*\[([^\]]*)\],?\s*)?
        (?:posts:\s*\[([^\]]*)\],?\s*)?
        (?:odds:\s*\[([^\]]*)\],?\s*)?
        (?:popularities:\s*\[([^\]]*)\],?\s*)?
        [^}]*\}
    '''
    
    # レースブロックごとに処理
    for match in re.finditer(detailed_pattern, content, re.VERBOSE | re.DOTALL):
        race_data = {
            'race_id': match.group(1),
            'date': date,
            'venue': venue,
            'race_number': int(match.group(4)) if match.group(4) else None,
            'race_name': match.group(5) if match.group(5) else '',
            'distance_str': match.group(7) if match.group(7) else '',
            'track_condition': match.group(8) if match.group(8) else '良',
        }
        
        # 距離とコースタイプを解析
        if race_data['distance_str']:
            dist_match = re.match(r'(芝|ダート)?(\d+)m', race_data['distance_str'])
            if dist_match:
                race_data['course_type'] = dist_match.group(1) or '芝'
                race_data['distance'] = int(dist_match.group(2))
            else:
                race_data['course_type'] = '芝'
                race_data['distance'] = 0
        
        # 馬名リストを解析
        if match.group(6):
            horses_str = match.group(6)
            # 引用符で囲まれた文字列を全て抽出
            horses = re.findall(r'"([^"]+)"', horses_str)
            race_data['horses'] = horses
        else:
            race_data['horses'] = []
        
        # 騎手リストを解析
        if match.group(9):
            jockeys_str = match.group(9)
            jockeys = re.findall(r'"([^"]+)"', jockeys_str)
            race_data['jockeys'] = jockeys
        else:
            race_data['jockeys'] = []
        
        # オッズリストを解析
        if match.group(11):
            odds_str = match.group(11)
            # 数値のみを抽出
            odds = re.findall(r'[\d.]+', odds_str)
            race_data['odds'] = [float(o) for o in odds]
        else:
            race_data['odds'] = []
        
        # 人気順位リストを解析
        if match.group(12):
            pop_str = match.group(12)
            popularities = re.findall(r'\d+', pop_str)
            race_data['popularities'] = [int(p) for p in popularities]
        else:
            race_data['popularities'] = []
        
        races.append(race_data)
    
    return {
        'filepath': filepath,
        'date': date,
        'venue': venue,
        'races': races
    }

def create_supabase_tables():
    """Supabaseにテーブルを作成するSQL文を生成"""
    
    sql = """
-- JRA中央競馬レース情報
CREATE TABLE IF NOT EXISTS jra_races (
    id SERIAL PRIMARY KEY,
    開催日 DATE NOT NULL,
    競馬場 VARCHAR(10) NOT NULL,
    レース番号 INT NOT NULL,
    レース名 VARCHAR(100),
    距離 INT,
    コース VARCHAR(10),
    グレード VARCHAR(20),
    天候 VARCHAR(10),
    馬場状態 VARCHAR(10),
    UNIQUE(開催日, 競馬場, レース番号)
);

-- 出走馬情報
CREATE TABLE IF NOT EXISTS jra_horses (
    id SERIAL PRIMARY KEY,
    race_id INT REFERENCES jra_races(id),
    馬番 INT NOT NULL,
    馬名 VARCHAR(50) NOT NULL,
    性齢 VARCHAR(10),
    斤量 DECIMAL(3,1),
    騎手名 VARCHAR(30),
    調教師名 VARCHAR(30),
    単勝オッズ DECIMAL(6,1),
    人気順位 INT,
    着順 INT,
    タイム VARCHAR(10),
    着差 VARCHAR(20)
);

-- エンジン予想結果
CREATE TABLE IF NOT EXISTS jra_predictions (
    id SERIAL PRIMARY KEY,
    race_id INT REFERENCES jra_races(id),
    エンジン名 VARCHAR(20) NOT NULL,
    予想1位 VARCHAR(50),
    予想1位スコア DECIMAL(5,1),
    予想2位 VARCHAR(50),
    予想2位スコア DECIMAL(5,1),
    予想3位 VARCHAR(50),
    予想3位スコア DECIMAL(5,1),
    予想4位 VARCHAR(50),
    予想4位スコア DECIMAL(5,1),
    予想5位 VARCHAR(50),
    予想5位スコア DECIMAL(5,1),
    予想作成日時 TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 払戻結果
CREATE TABLE IF NOT EXISTS jra_payouts (
    id SERIAL PRIMARY KEY,
    race_id INT REFERENCES jra_races(id),
    単勝_馬番 INT,
    単勝_払戻金 INT,
    複勝1_馬番 INT,
    複勝1_払戻金 INT,
    複勝2_馬番 INT,
    複勝2_払戻金 INT,
    複勝3_馬番 INT,
    複勝3_払戻金 INT,
    馬連_馬番1 INT,
    馬連_馬番2 INT,
    馬連_払戻金 INT,
    三連複_馬番1 INT,
    三連複_馬番2 INT,
    三連複_馬番3 INT,
    三連複_払戻金 INT,
    三連単_馬番1 INT,
    三連単_馬番2 INT,
    三連単_馬番3 INT,
    三連単_払戻金 INT,
    UNIQUE(race_id)
);
    """
    
    print("=" * 60)
    print("Supabaseテーブル作成SQL")
    print("=" * 60)
    print(sql)
    print("=" * 60)
    print("このSQLをSupabaseのSQL Editorで実行してください")
    print("=" * 60)

def generate_csv_data(parsed_data: Dict[str, Any]) -> List[Dict]:
    """パースしたデータをCSV形式に変換"""
    
    csv_rows = []
    
    for race in parsed_data['races']:
        # レース基本情報
        race_row = {
            '開催日': parsed_data['date'],
            '競馬場': parsed_data['venue'],
            'レース番号': race['race_number'],
            'レース名': race['race_name'],
            '距離': race.get('distance', 0),
            'コース': race.get('course_type', '芝'),
            '馬場状態': race['track_condition'],
            '出走頭数': len(race['horses'])
        }
        
        # 各馬の情報を追加
        for i, horse_name in enumerate(race['horses']):
            horse_row = race_row.copy()
            horse_row['馬番'] = i + 1
            horse_row['馬名'] = horse_name
            
            if i < len(race['jockeys']):
                horse_row['騎手'] = race['jockeys'][i]
            
            if i < len(race['odds']):
                horse_row['オッズ'] = race['odds'][i]
            
            if i < len(race['popularities']):
                horse_row['人気'] = race['popularities'][i]
            
            csv_rows.append(horse_row)
    
    return csv_rows

def main():
    """メイン処理"""
    
    print("=" * 60)
    print("TSファイル → Supabase同期処理")
    print("=" * 60)
    
    # まずテーブル作成SQLを表示
    create_supabase_tables()
    
    # TSファイルの一覧を取得
    ts_dir = '/mnt/e/dev/Cusor/front/d-logic-ai-frontend/src/data/archive'
    ts_files = glob.glob(os.path.join(ts_dir, 'races-*.ts'))
    
    print(f"\n{len(ts_files)}個のTSファイルを検出")
    
    all_races = []
    
    for ts_file in sorted(ts_files)[:5]:  # まず5ファイルでテスト
        print(f"\n処理中: {os.path.basename(ts_file)}")
        
        parsed = parse_ts_file(ts_file)
        if parsed:
            print(f"  → {len(parsed['races'])}レース検出")
            
            # CSV形式のデータを生成
            csv_data = generate_csv_data(parsed)
            all_races.extend(csv_data)
            
            # 最初のレースの情報を表示
            if parsed['races']:
                first_race = parsed['races'][0]
                print(f"  → 例: R{first_race['race_number']} {first_race['race_name']}")
                print(f"       {len(first_race['horses'])}頭立て")
    
    # CSVファイルとして出力（確認用）
    import csv
    csv_file = '/mnt/e/dev/Cusor/chatbot/uma/backend/data/jra_races_sample.csv'
    
    if all_races:
        # CSVファイルに書き出し
        keys = all_races[0].keys()
        with open(csv_file, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(all_races)
        
        print(f"\n✅ サンプルCSVファイル作成: {csv_file}")
        print(f"   {len(all_races)}行のデータ")
    
    print("\n" + "=" * 60)
    print("次のステップ:")
    print("1. Supabaseでテーブルを作成")
    print("2. CSVファイルを確認")
    print("3. Supabase接続情報を設定")
    print("4. データのインポート実行")
    print("=" * 60)

if __name__ == "__main__":
    main()