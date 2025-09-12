#!/usr/bin/env python3
"""
TSファイルからSupabaseへのインポート（修正版）
競馬場名、レース名、距離を正しく取得
"""

import os
import sys
import re
import json
import glob
import logging
from datetime import datetime
from typing import List, Dict, Any

# Supabase設定
from supabase import create_client
from dotenv import load_dotenv

# 環境変数読み込み
load_dotenv()

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Supabase接続
SUPABASE_URL = os.getenv('NEXT_PUBLIC_SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    logger.error("環境変数が設定されていません")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ================================
# TSファイルパーサー（改良版）
# ================================

def parse_ts_file(filepath: str) -> Dict[str, Any]:
    """TSファイルをパースして構造化データに変換"""
    
    logger.info(f"ファイル解析: {filepath}")
    
    filename = os.path.basename(filepath)
    
    # ファイル名から日付を抽出
    match = re.match(r'races-(\d{8})', filename)
    if not match:
        logger.warning(f"ファイル名が想定外: {filename}")
        return None
    
    date_str = match.group(1)
    date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # レースデータを抽出
    races = []
    
    # レースブロックを抽出（改良版）
    race_blocks = re.findall(r'\{[^{}]*race_id:[^{}]*?(?:\{[^{}]*\}[^{}]*)*?\}', content, re.DOTALL)
    
    for block in race_blocks:
        race_data = {}
        
        # venue（競馬場）- 必須
        match = re.search(r'venue:\s*"([^"]*)"', block)
        if match:
            race_data['venue'] = match.group(1)
        else:
            # venueがない場合はファイル名から推測
            if '中山' in filename:
                race_data['venue'] = '中山'
            elif '阪神' in filename:
                race_data['venue'] = '阪神'
            elif '札幌' in filename:
                race_data['venue'] = '札幌'
            elif '新潟' in filename or 'niigata' in filename:
                race_data['venue'] = '新潟'
            elif '中京' in filename or 'chukyo' in filename:
                race_data['venue'] = '中京'
            else:
                race_data['venue'] = 'unknown'
        
        # race_number
        match = re.search(r'race_number:\s*(\d+)', block)
        if match:
            race_data['race_number'] = int(match.group(1))
        
        # race_name
        match = re.search(r'race_name:\s*"([^"]*)"', block)
        if match:
            race_data['race_name'] = match.group(1)
        
        # distance
        match = re.search(r'distance:\s*"([^"]*)"', block)
        if match:
            distance_str = match.group(1)
            # "芝1600m" または "ダ1800m" → コース: "芝/ダート", 距離: 1600/1800
            dist_match = re.match(r'(芝|ダ|ダート)?(\d+)m', distance_str)
            if dist_match:
                course = dist_match.group(1) or '芝'
                if course == 'ダ':
                    course = 'ダート'
                race_data['course_type'] = course
                race_data['distance'] = int(dist_match.group(2))
        
        # track_condition
        match = re.search(r'track_condition:\s*"([^"]*)"', block)
        if match:
            race_data['track_condition'] = match.group(1)
        
        # horses
        match = re.search(r'horses:\s*\[([^\]]*)\]', block, re.DOTALL)
        if match:
            horses_str = match.group(1)
            horses = re.findall(r'"([^"]+)"', horses_str)
            race_data['horses'] = horses
        
        # jockeys
        match = re.search(r'jockeys:\s*\[([^\]]*)\]', block, re.DOTALL)
        if match:
            jockeys_str = match.group(1)
            jockeys = re.findall(r'"([^"]+)"', jockeys_str)
            race_data['jockeys'] = jockeys
        
        # odds
        match = re.search(r'odds:\s*\[([^\]]*)\]', block, re.DOTALL)
        if match:
            odds_str = match.group(1)
            odds = re.findall(r'[\d.]+', odds_str)
            race_data['odds'] = [float(o) for o in odds]
        
        # popularities
        match = re.search(r'popularities:\s*\[([^\]]*)\]', block, re.DOTALL)
        if match:
            pop_str = match.group(1)
            popularities = re.findall(r'\d+', pop_str)
            race_data['popularities'] = [int(p) for p in popularities]
        
        if 'race_number' in race_data and 'horses' in race_data:
            races.append(race_data)
    
    return {
        'date': date,
        'races': races
    }

# ================================
# Supabaseインポート
# ================================

def import_races_to_supabase(parsed_data: Dict[str, Any]) -> List[int]:
    """パースしたデータをSupabaseにインポート"""
    
    race_ids = []
    
    for race in parsed_data['races']:
        # レース基本情報
        venue = race.get('venue', 'unknown')
        race_record = {
            '開催日': parsed_data['date'],
            '競馬場': venue,
            'レース番号': race.get('race_number', 0),
            'レース名': race.get('race_name', ''),
            '距離': race.get('distance', 0),
            'コース': race.get('course_type', ''),
            '天候': '',  # TSファイルには含まれていない
            '馬場状態': race.get('track_condition', '')
        }
        
        try:
            # 既存レースをチェック
            existing = supabase.table('jra_races').select('id').eq(
                '開催日', race_record['開催日']
            ).eq(
                '競馬場', race_record['競馬場']
            ).eq(
                'レース番号', race_record['レース番号']
            ).execute()
            
            if existing.data:
                race_id = existing.data[0]['id']
                logger.info(f"既存レース: {race_record['開催日']} {race_record['競馬場']} R{race_record['レース番号']}")
            else:
                # 新規登録
                result = supabase.table('jra_races').insert(race_record).execute()
                race_id = result.data[0]['id']
                logger.info(f"新規レース登録: {race_record['開催日']} {race_record['競馬場']} R{race_record['レース番号']}")
            
            race_ids.append(race_id)
            
            # 出走馬情報を登録
            if 'horses' in race:
                # 既存データを削除
                supabase.table('jra_horses').delete().eq('race_id', race_id).execute()
                
                # 新規登録
                horse_records = []
                for i, horse_name in enumerate(race['horses']):
                    horse_record = {
                        'race_id': race_id,
                        '馬番': i + 1,
                        '馬名': horse_name,
                        '騎手名': race['jockeys'][i] if i < len(race.get('jockeys', [])) else '',
                        '単勝オッズ': race['odds'][i] if i < len(race.get('odds', [])) else 0,
                        '人気順位': race['popularities'][i] if i < len(race.get('popularities', [])) else 0
                    }
                    horse_records.append(horse_record)
                
                if horse_records:
                    supabase.table('jra_horses').insert(horse_records).execute()
                    logger.info(f"  → {len(horse_records)}頭の馬情報を登録")
                    
        except Exception as e:
            logger.error(f"エラー: {e}")
    
    return race_ids

# ================================
# エンジン分析（ダミー実装）
# ================================

def analyze_with_engines(race_id: int, horses: List[str]) -> None:
    """各エンジンでレースを分析してSupabaseに保存"""
    
    engines = ['D-Logic', 'I-Logic', 'ViewLogic']
    
    for engine in engines:
        # ダミーの予想
        if len(horses) >= 5:
            prediction = {
                'race_id': race_id,
                'エンジン名': engine,
                '予想1位': horses[0],
                '予想1位スコア': 75.0,
                '予想2位': horses[1],
                '予想2位スコア': 70.0,
                '予想3位': horses[2],
                '予想3位スコア': 65.0,
                '予想4位': horses[3],
                '予想4位スコア': 60.0,
                '予想5位': horses[4],
                '予想5位スコア': 55.0
            }
            
            try:
                # 既存の予想を削除
                supabase.table('jra_predictions').delete().eq(
                    'race_id', race_id
                ).eq(
                    'エンジン名', engine
                ).execute()
                
                # 新規挿入
                supabase.table('jra_predictions').insert(prediction).execute()
                logger.info(f"  → {engine}の予想を登録")
            except Exception as e:
                logger.error(f"予想登録エラー: {e}")

# ================================
# メイン処理
# ================================

def main():
    """メイン処理"""
    
    logger.info("=" * 60)
    logger.info("TSファイル → Supabase インポート処理（修正版）")
    logger.info("=" * 60)
    
    # TSファイルの一覧を取得
    ts_dir = '/mnt/e/dev/Cusor/front/d-logic-ai-frontend/src/data/archive'
    ts_files = glob.glob(os.path.join(ts_dir, 'races-*.ts'))
    
    logger.info(f"{len(ts_files)}個のTSファイルを検出")
    
    # 8月31日以降のファイルのみ処理
    for ts_file in sorted(ts_files):
        # ファイル名から日付を抽出
        filename = os.path.basename(ts_file)
        match = re.search(r'races-([0-9]{8})', filename)
        if not match:
            continue
            
        file_date = match.group(1)
        # 20250831以降のファイルのみ処理
        if file_date < '20250831':
            logger.info(f"スキップ: {filename} (8月31日より前)")
            continue
        
        logger.info(f"\n処理中: {os.path.basename(ts_file)}")
        
        # 1. TSファイルをパース
        parsed = parse_ts_file(ts_file)
        if not parsed or not parsed['races']:
            continue
        
        logger.info(f"  → {len(parsed['races'])}レース検出")
        
        # 2. Supabaseにインポート
        race_ids = import_races_to_supabase(parsed)
        
        # 3. エンジン分析（各レースごと）
        for i, race_id in enumerate(race_ids):
            if i < len(parsed['races']):
                race = parsed['races'][i]
                if 'horses' in race:
                    horses = race['horses']
                    analyze_with_engines(race_id, horses)
    
    logger.info("\n" + "=" * 60)
    logger.info("インポート処理完了")
    logger.info("=" * 60)

if __name__ == '__main__':
    main()