#!/usr/bin/env python3
"""
既存のTSファイルをSupabaseに同期するスクリプト
人間が見てわかりやすいデータ構造で保存
"""

import os
import re
import json
from datetime import datetime
from typing import Dict, List, Any
import glob
from supabase import create_client, Client

# Supabase設定（環境変数から取得）
SUPABASE_URL = os.getenv('SUPABASE_URL', 'your-supabase-url')
SUPABASE_KEY = os.getenv('SUPABASE_ANON_KEY', 'your-anon-key')

# Supabaseクライアント
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def parse_ts_file(filepath: str) -> Dict[str, Any]:
    """TSファイルをパースしてPython辞書に変換"""
    
    # ファイル名から情報抽出
    filename = os.path.basename(filepath)
    # races-20250907-中山.ts のようなファイル名を想定
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
    
    # TSファイルから各レースのデータを抽出
    races = []
    
    # 正規表現でレースデータを抽出（簡易版）
    # 実際のTSファイル構造に合わせて調整が必要
    race_pattern = r'\{[^}]+race_number:[^}]+\}'
    
    # より詳細なパース（実際のTS構造に応じて調整）
    # ここは実際のTSファイルの構造を見て適切に実装する必要があります
    
    return {
        'date': date,
        'venue': venue,
        'filepath': filepath,
        'races': races  # パースしたレースデータ
    }

def sync_race_to_supabase(race_data: Dict[str, Any]) -> int:
    """レース情報をSupabaseに保存"""
    
    # レース基本情報を保存
    race_record = {
        '開催日': race_data['date'],
        '競馬場': race_data['venue'],
        'レース番号': race_data.get('race_number', 1),
        'レース名': race_data.get('race_name', ''),
        '距離': race_data.get('distance', 0),
        'コース': race_data.get('course_type', '芝'),
        'グレード': race_data.get('grade', ''),
        '天候': race_data.get('weather', ''),
        '馬場状態': race_data.get('track_condition', '')
    }
    
    # Supabaseに挿入
    result = supabase.table('jra_races').insert(race_record).execute()
    
    if result.data:
        race_id = result.data[0]['id']
        print(f"レース登録完了: {race_data['date']} {race_data['venue']} R{race_record['レース番号']}")
        return race_id
    
    return None

def sync_horses_to_supabase(race_id: int, horses_data: List[Dict]) -> None:
    """出走馬情報をSupabaseに保存"""
    
    horse_records = []
    
    for horse in horses_data:
        record = {
            'race_id': race_id,
            '馬番': horse.get('horse_number', 0),
            '馬名': horse.get('horse_name', ''),
            '性齢': horse.get('age_sex', ''),
            '斤量': horse.get('weight', 0),
            '騎手名': horse.get('jockey', ''),
            '調教師名': horse.get('trainer', ''),
            '単勝オッズ': horse.get('odds', 0),
            '人気順位': horse.get('popularity', 0)
        }
        horse_records.append(record)
    
    if horse_records:
        result = supabase.table('jra_horses').insert(horse_records).execute()
        print(f"  → {len(horse_records)}頭の馬情報を登録")

def analyze_with_engines(race_id: int, race_data: Dict) -> None:
    """各エンジンでレースを分析（ダミー実装）"""
    
    # ここで実際のエンジン分析を実行
    # 現在はダミーデータ
    
    engines = ['D-Logic', 'I-Logic', 'ViewLogic']
    
    for engine in engines:
        prediction = {
            'race_id': race_id,
            'エンジン名': engine,
            '予想1位': 'ダミー馬名1',
            '予想1位スコア': 75.0,
            '予想2位': 'ダミー馬名2',
            '予想2位スコア': 70.0,
            '予想3位': 'ダミー馬名3',
            '予想3位スコア': 65.0,
            '予想4位': 'ダミー馬名4',
            '予想4位スコア': 60.0,
            '予想5位': 'ダミー馬名5',
            '予想5位スコア': 55.0
        }
        
        result = supabase.table('jra_predictions').insert(prediction).execute()
        print(f"  → {engine}の予想を登録")

def main():
    """メイン処理"""
    print("=" * 60)
    print("TSファイル → Supabase 同期処理")
    print("=" * 60)
    
    # TSファイルのパスを取得
    ts_files = glob.glob('/mnt/e/dev/Cusor/front/d-logic-ai-frontend/src/data/archive/races-*.ts')
    
    print(f"\n{len(ts_files)}個のTSファイルを検出")
    
    success_count = 0
    error_count = 0
    
    for ts_file in ts_files:
        try:
            print(f"\n処理中: {os.path.basename(ts_file)}")
            
            # TSファイルをパース
            parsed_data = parse_ts_file(ts_file)
            if not parsed_data:
                error_count += 1
                continue
            
            # レース情報を同期
            # 実際には parsed_data['races'] をループ処理
            race_id = sync_race_to_supabase(parsed_data)
            
            if race_id:
                # 出走馬情報を同期
                # sync_horses_to_supabase(race_id, parsed_data.get('horses', []))
                
                # エンジン分析を実行
                # analyze_with_engines(race_id, parsed_data)
                
                success_count += 1
            else:
                error_count += 1
                
        except Exception as e:
            print(f"  エラー: {e}")
            error_count += 1
    
    print("\n" + "=" * 60)
    print(f"同期完了: 成功 {success_count}件 / エラー {error_count}件")
    print("=" * 60)

if __name__ == "__main__":
    # 環境変数チェック
    if SUPABASE_URL == 'your-supabase-url':
        print("エラー: SUPABASE_URL環境変数を設定してください")
        print("export SUPABASE_URL='https://xxxxx.supabase.co'")
        print("export SUPABASE_ANON_KEY='your-anon-key'")
    else:
        main()