#!/usr/bin/env python3
"""
9/7と9/13の欠損データを修正
シングルクォートとダブルクォートの両方に対応
"""

import os
import sys
import re
import glob
import logging
from supabase import create_client

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Supabase接続
SUPABASE_URL = os.getenv('NEXT_PUBLIC_SUPABASE_URL', 'https://veklxmosegqkjtvjbksd.supabase.co')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZla2x4bW9zZWdxa2p0dmpia3NkIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NDcyODYxNiwiZXhwIjoyMDcwMzA0NjE2fQ.z8ahiNtn04kIjgNFyKXb8zAcSEj6BoEIxIc789dZZ-k')

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def parse_ts_file_fixed(filepath):
    """修正版パーサー：シングルクォートも処理"""
    
    logger.info(f"ファイル解析: {filepath}")
    
    filename = os.path.basename(filepath)
    
    # ファイル名から日付を抽出
    match = re.match(r'races-(\d{8})', filename)
    if not match:
        return None
    
    date_str = match.group(1)
    date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # レースデータを抽出
    races = []
    
    # レースブロックを抽出（より柔軟なパターン）
    race_blocks = re.findall(r'\{[^{}]*race_id:[^{}]*?(?:\{[^{}]*\}[^{}]*)*?\}', content, re.DOTALL)
    
    for block in race_blocks:
        race_data = {}
        
        # venue（競馬場）
        match = re.search(r'venue:\s*["\']([^"\']*)["\']', block)
        if match:
            race_data['venue'] = match.group(1)
        else:
            # ファイル名から推測
            if '中山' in filename:
                race_data['venue'] = '中山'
            elif '阪神' in filename:
                race_data['venue'] = '阪神'
            elif '札幌' in filename:
                race_data['venue'] = '札幌'
            elif '新潟' in filename:
                race_data['venue'] = '新潟'
            elif '中京' in filename:
                race_data['venue'] = '中京'
            else:
                race_data['venue'] = 'unknown'
        
        # race_number
        match = re.search(r'race_number:\s*(\d+)', block)
        if match:
            race_data['race_number'] = int(match.group(1))
        
        # race_name（シングル/ダブルクォート対応）
        match = re.search(r'race_name:\s*["\']([^"\']*)["\']', block)
        if match:
            race_data['race_name'] = match.group(1)
        
        # distance（シングル/ダブルクォート対応）
        match = re.search(r'distance:\s*["\']([^"\']*)["\']', block)
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
        
        # track_condition（シングル/ダブルクォート対応）
        match = re.search(r'track_condition:\s*["\']([^"\']*)["\']', block)
        if match:
            race_data['track_condition'] = match.group(1)
        
        # horses（配列処理）
        match = re.search(r'horses:\s*\[([^\]]*)\]', block, re.DOTALL)
        if match:
            horses_str = match.group(1)
            horses = re.findall(r'["\']([^"\']+)["\']', horses_str)
            race_data['horses'] = horses
        
        # jockeys（配列処理）
        match = re.search(r'jockeys:\s*\[([^\]]*)\]', block, re.DOTALL)
        if match:
            jockeys_str = match.group(1)
            jockeys = re.findall(r'["\']([^"\']+)["\']', jockeys_str)
            race_data['jockeys'] = jockeys
        
        # odds（配列処理）
        match = re.search(r'odds:\s*\[([^\]]*)\]', block, re.DOTALL)
        if match:
            odds_str = match.group(1)
            odds = re.findall(r'[\d.]+', odds_str)
            race_data['odds'] = [float(o) for o in odds]
        
        # popularities（配列処理）
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

def update_race_data(parsed_data):
    """欠損データを更新"""
    
    for race in parsed_data['races']:
        # 既存レースを取得
        existing = supabase.table('jra_races').select('*').eq(
            '開催日', parsed_data['date']
        ).eq(
            '競馬場', race.get('venue', 'unknown')
        ).eq(
            'レース番号', race.get('race_number', 0)
        ).execute()
        
        if existing.data:
            race_record = existing.data[0]
            
            # データが空の場合のみ更新
            if not race_record.get('レース名') or not race_record.get('距離') or race_record.get('距離') == 0:
                update_data = {}
                
                if race.get('race_name') and not race_record.get('レース名'):
                    update_data['レース名'] = race['race_name']
                
                if race.get('distance') and (not race_record.get('距離') or race_record.get('距離') == 0):
                    update_data['距離'] = race['distance']
                
                if race.get('course_type') and not race_record.get('コース'):
                    update_data['コース'] = race['course_type']
                
                if race.get('track_condition') and not race_record.get('馬場状態'):
                    update_data['馬場状態'] = race['track_condition']
                
                if update_data:
                    supabase.table('jra_races').update(update_data).eq('id', race_record['id']).execute()
                    logger.info(f"更新: {parsed_data['date']} {race['venue']} R{race['race_number']}")

def main():
    """メイン処理"""
    
    logger.info("=" * 60)
    logger.info("欠損データ修正処理")
    logger.info("=" * 60)
    
    # 9/7と9/13のファイルを処理
    ts_dir = '/mnt/e/dev/Cusor/front/d-logic-ai-frontend/src/data/archive'
    
    # 処理対象ファイル
    target_patterns = [
        'races-20250907*.ts',
        'races-20250913*.ts'
    ]
    
    for pattern in target_patterns:
        files = glob.glob(os.path.join(ts_dir, pattern))
        
        for ts_file in sorted(files):
            logger.info(f"\n処理中: {os.path.basename(ts_file)}")
            
            # パース
            parsed = parse_ts_file_fixed(ts_file)
            if not parsed or not parsed['races']:
                continue
            
            logger.info(f"  → {len(parsed['races'])}レース検出")
            
            # データ更新
            update_race_data(parsed)
    
    # 結果確認
    logger.info("\n" + "=" * 60)
    logger.info("処理完了 - データ品質確認")
    
    # 空データの確認
    empty_check = supabase.table('jra_races').select('*').or_('レース名.is.null,距離.eq.0').execute()
    logger.info(f"残りの欠損データ: {len(empty_check.data)}件")
    
    if len(empty_check.data) == 0:
        logger.info("✅ 全てのデータが正常に修正されました！")

if __name__ == '__main__':
    main()