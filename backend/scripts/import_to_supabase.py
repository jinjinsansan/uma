#!/usr/bin/env python3
"""
1. TSファイルからSupabaseへレースデータをインポート
2. 各エンジンで分析してSupabaseへ保存
3. netkeibaのMySQLから払い戻し結果を取得してSupabaseへ保存
"""

import os
import re
import json
import glob
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from typing import Dict, List, Any, Optional
from supabase import create_client, Client
import logging

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ================================
# 設定
# ================================

# Supabase設定（環境変数から取得）
SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://your-project.supabase.co')
# Service Role Keyを使用（RLSをバイパス）
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY', os.getenv('SUPABASE_ANON_KEY', 'your-anon-key'))

# pckeiba PostgreSQL設定（JRA速報系データ）
PCKEIBA_CONFIG = {
    'host': '172.25.160.1',  # WSL2からWindowsのPostgreSQL
    'port': 5432,
    'database': 'pckeiba',
    'user': 'postgres',
    'password': 'postgres'
}

# Supabaseクライアント
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ================================
# 1. TSファイルからレースデータをインポート
# ================================

def parse_ts_file(filepath: str) -> Optional[Dict[str, Any]]:
    """TSファイルをパースしてレース情報を抽出"""
    
    filename = os.path.basename(filepath)
    
    # ファイル名から日付と会場を抽出
    # races-20250907-中山.ts または races-20250830-chukyo.ts のパターン
    match = re.match(r'races-(\d{8})(?:-(.+))?\.ts', filename)
    if not match:
        logger.warning(f"ファイル名が想定外: {filename}")
        return None
    
    date_str = match.group(1)
    venue = match.group(2) if match.group(2) else 'unknown'
    
    # 日付をYYYY-MM-DD形式に変換
    date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # レースデータを抽出（改良版パターン）
    races = []
    
    # レースブロックを抽出
    race_blocks = re.findall(r'\{[^{}]*race_id:[^{}]*?\}', content, re.DOTALL)
    
    for block in race_blocks:
        # 各フィールドを抽出
        race_data = {}
        
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
            # "芝1600m" → コース: "芝", 距離: 1600
            dist_match = re.match(r'(芝|ダート)?(\d+)m', distance_str)
            if dist_match:
                race_data['course_type'] = dist_match.group(1) or '芝'
                race_data['distance'] = int(dist_match.group(2))
        
        # track_condition
        match = re.search(r'track_condition:\s*"([^"]*)"', block)
        if match:
            race_data['track_condition'] = match.group(1)
        
        # horses
        match = re.search(r'horses:\s*\[([^\]]*)\]', block)
        if match:
            horses_str = match.group(1)
            horses = re.findall(r'"([^"]+)"', horses_str)
            race_data['horses'] = horses
        
        # jockeys
        match = re.search(r'jockeys:\s*\[([^\]]*)\]', block)
        if match:
            jockeys_str = match.group(1)
            jockeys = re.findall(r'"([^"]+)"', jockeys_str)
            race_data['jockeys'] = jockeys
        
        # odds
        match = re.search(r'odds:\s*\[([^\]]*)\]', block)
        if match:
            odds_str = match.group(1)
            odds = re.findall(r'[\d.]+', odds_str)
            race_data['odds'] = [float(o) for o in odds]
        
        # popularities
        match = re.search(r'popularities:\s*\[([^\]]*)\]', block)
        if match:
            pop_str = match.group(1)
            popularities = re.findall(r'\d+', pop_str)
            race_data['popularities'] = [int(p) for p in popularities]
        
        race_data['date'] = date
        race_data['venue'] = venue
        
        if 'race_number' in race_data:
            races.append(race_data)
    
    return {
        'filepath': filepath,
        'date': date,
        'venue': venue,
        'races': races
    }

def import_races_to_supabase(parsed_data: Dict[str, Any]) -> List[int]:
    """レースデータをSupabaseにインポート"""
    
    race_ids = []
    
    for race in parsed_data['races']:
        # レース基本情報を挿入
        race_record = {
            '開催日': race['date'],
            '競馬場': race['venue'],
            'レース番号': race.get('race_number', 0),
            'レース名': race.get('race_name', ''),
            '距離': race.get('distance', 0),
            'コース': race.get('course_type', '芝'),
            '馬場状態': race.get('track_condition', '良')
        }
        
        try:
            # 既存レコードをチェック
            existing = supabase.table('jra_races').select('id').eq(
                '開催日', race_record['開催日']
            ).eq(
                '競馬場', race_record['競馬場']
            ).eq(
                'レース番号', race_record['レース番号']
            ).execute()
            
            if existing.data:
                race_id = existing.data[0]['id']
                logger.info(f"既存レース: {race['date']} {race['venue']} R{race.get('race_number')}")
            else:
                result = supabase.table('jra_races').insert(race_record).execute()
                race_id = result.data[0]['id']
                logger.info(f"新規レース登録: {race['date']} {race['venue']} R{race.get('race_number')}")
            
            race_ids.append(race_id)
            
            # 出走馬情報を挿入
            if 'horses' in race:
                horse_records = []
                for i, horse_name in enumerate(race['horses']):
                    horse_record = {
                        'race_id': race_id,
                        '馬番': i + 1,
                        '馬名': horse_name,
                        '騎手名': race['jockeys'][i] if i < len(race.get('jockeys', [])) else None,
                        '単勝オッズ': race['odds'][i] if i < len(race.get('odds', [])) else None,
                        '人気順位': race['popularities'][i] if i < len(race.get('popularities', [])) else None
                    }
                    horse_records.append(horse_record)
                
                if horse_records:
                    # 既存の馬データを削除（重複防止）
                    supabase.table('jra_horses').delete().eq('race_id', race_id).execute()
                    # 新規挿入
                    supabase.table('jra_horses').insert(horse_records).execute()
                    logger.info(f"  → {len(horse_records)}頭の馬情報を登録")
                    
        except Exception as e:
            logger.error(f"エラー: {e}")
    
    return race_ids

# ================================
# 2. エンジン分析（ダミー実装）
# ================================

def analyze_with_engines(race_id: int, horses: List[str]) -> None:
    """各エンジンでレースを分析してSupabaseに保存"""
    
    # TODO: 実際のエンジン分析を実装
    # 現在はダミーデータ
    
    engines = ['D-Logic', 'I-Logic', 'ViewLogic']
    
    for engine in engines:
        # ダミーの予想（実際には各エンジンを呼び出す）
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
# 3. netkeibaから払い戻し結果を取得
# ================================

def fetch_payout_from_pckeiba(date: str, venue: str, race_number: int) -> Optional[Dict]:
    """pckeibaのPostgreSQLから払い戻し結果を取得"""
    
    try:
        conn = psycopg2.connect(**PCKEIBA_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # 競馬場コード変換
        venue_code = {
            '札幌': '01', '函館': '02', '福島': '03', '新潟': '04',
            '東京': '05', '中山': '06', '中京': '07', '京都': '08',
            '阪神': '09', '小倉': '10'
        }.get(venue, '06')  # デフォルトは中山
        
        # 日付フォーマット変換 (YYYY-MM-DD → YYYYMMDD)
        date_code = date.replace('-', '')
        
        # 払い戻しデータ取得クエリ（jvd_hrテーブルから）
        query = """
        SELECT 
            tansho_umaban,
            tansho_haraimodoshi,
            fukusho_umaban_1,
            fukusho_haraimodoshi_1,
            fukusho_umaban_2,
            fukusho_haraimodoshi_2,
            fukusho_umaban_3,
            fukusho_haraimodoshi_3,
            umaren_umaban_1,
            umaren_umaban_2,
            umaren_haraimodoshi,
            umatan_umaban_1,
            umatan_umaban_2,
            umatan_haraimodoshi,
            sanrenpuku_umaban_1,
            sanrenpuku_umaban_2,
            sanrenpuku_umaban_3,
            sanrenpuku_haraimodoshi,
            sanrentan_umaban_1,
            sanrentan_umaban_2,
            sanrentan_umaban_3,
            sanrentan_haraimodoshi
        FROM jvd_hr
        WHERE kaisai_nen = %s 
        AND kaisai_tsukihi = %s
        AND jyo_code = %s
        AND race_bango = %s
        """
        
        year = date[:4]
        monthday = date[5:7] + date[8:10]
        
        cursor.execute(query, (year, monthday, venue_code, race_number))
        result = cursor.fetchone()
        
        if result:
            # 払い戻しデータを整形
            payout_data = {
                '単勝_馬番': result.get('tansho_umaban'),
                '単勝_払戻金': result.get('tansho_haraimodoshi'),
                '複勝1_馬番': result.get('fukusho_umaban_1'),
                '複勝1_払戻金': result.get('fukusho_haraimodoshi_1'),
                '複勝2_馬番': result.get('fukusho_umaban_2'),
                '複勝2_払戻金': result.get('fukusho_haraimodoshi_2'),
                '複勝3_馬番': result.get('fukusho_umaban_3'),
                '複勝3_払戻金': result.get('fukusho_haraimodoshi_3'),
                '馬連_馬番1': result.get('umaren_umaban_1'),
                '馬連_馬番2': result.get('umaren_umaban_2'),
                '馬連_払戻金': result.get('umaren_haraimodoshi'),
                '馬単_馬番1': result.get('umatan_umaban_1'),
                '馬単_馬番2': result.get('umatan_umaban_2'),
                '馬単_払戻金': result.get('umatan_haraimodoshi'),
                '三連複_馬番1': result.get('sanrenpuku_umaban_1'),
                '三連複_馬番2': result.get('sanrenpuku_umaban_2'),
                '三連複_馬番3': result.get('sanrenpuku_umaban_3'),
                '三連複_払戻金': result.get('sanrenpuku_haraimodoshi'),
                '三連単_馬番1': result.get('sanrentan_umaban_1'),
                '三連単_馬番2': result.get('sanrentan_umaban_2'),
                '三連単_馬番3': result.get('sanrentan_umaban_3'),
                '三連単_払戻金': result.get('sanrentan_haraimodoshi')
            }
            return payout_data
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"MySQL接続エラー: {e}")
        return None

def save_payout_to_supabase(race_id: int, payout_data: Dict) -> None:
    """払い戻し結果をSupabaseに保存"""
    
    if not payout_data:
        return
    
    payout_record = {
        'race_id': race_id,
        **payout_data
    }
    
    try:
        # 既存のデータを削除
        supabase.table('jra_payouts').delete().eq('race_id', race_id).execute()
        
        # 新規挿入
        supabase.table('jra_payouts').insert(payout_record).execute()
        logger.info(f"  → 払い戻し結果を登録")
    except Exception as e:
        logger.error(f"払い戻し登録エラー: {e}")

# ================================
# メイン処理
# ================================

def main():
    """メイン処理"""
    
    logger.info("=" * 60)
    logger.info("TSファイル → Supabase インポート処理")
    logger.info("=" * 60)
    
    # TSファイルの一覧を取得
    ts_dir = '/mnt/e/dev/Cusor/front/d-logic-ai-frontend/src/data/archive'
    ts_files = glob.glob(os.path.join(ts_dir, 'races-*.ts'))
    
    logger.info(f"{len(ts_files)}個のTSファイルを検出")
    
    # 8月31日以降のファイルのみ処理
    from datetime import datetime
    
    for ts_file in sorted(ts_files):
        # ファイル名から日付を抽出 (races-YYYYMMDD-*.ts or races-YYYYMMDD.ts)
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
                    analyze_with_engines(race_id, race['horses'])
        
        # 4. 払い戻し結果を取得（pckeiba PostgreSQL → Supabase）
        for i, race_id in enumerate(race_ids):
            if i < len(parsed['races']):
                race = parsed['races'][i]
                payout = fetch_payout_from_pckeiba(
                    race['date'],
                    race['venue'],
                    race.get('race_number', 0)
                )
                if payout:
                    save_payout_to_supabase(race_id, payout)
    
    logger.info("\n" + "=" * 60)
    logger.info("インポート処理完了")
    logger.info("=" * 60)

if __name__ == "__main__":
    # 環境変数チェック
    if SUPABASE_URL == 'https://your-project.supabase.co':
        print("エラー: 環境変数を設定してください")
        print("export SUPABASE_URL='https://xxxxx.supabase.co'")
        print("export SUPABASE_ANON_KEY='your-anon-key'")
    else:
        main()