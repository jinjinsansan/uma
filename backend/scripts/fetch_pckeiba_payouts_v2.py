#!/usr/bin/env python3
"""
pckeiba PostgreSQLから払い戻し結果を取得してSupabaseに保存（実装版）
"""

import os
import psycopg2
from datetime import datetime
from typing import Dict, List, Optional
from supabase import create_client, Client
from dotenv import load_dotenv
import logging

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# .envファイルの読み込み
load_dotenv()

# Supabase設定
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_KEY')

# pckeiba PostgreSQL設定
PCKEIBA_CONFIG = {
    'host': '172.25.160.1',
    'port': 5432,
    'database': 'pckeiba',
    'user': 'postgres',
    'password': 'postgres'
}

# Supabaseクライアント初期化
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# 競馬場コードマッピング
VENUE_MAPPING = {
    '札幌': '01',
    '函館': '02',
    '福島': '03',
    '新潟': '04',
    '東京': '05',
    '中山': '06',
    '中京': '07',
    '京都': '08',
    '阪神': '09',
    '小倉': '10'
}

def get_payout_from_pckeiba(date_str: str, venue: str, race_num: int) -> Dict:
    """
    pckeibaから払い戻しデータを取得
    
    Args:
        date_str: 日付（YYYY-MM-DD形式）
        venue: 競馬場名
        race_num: レース番号
    """
    try:
        conn = psycopg2.connect(**PCKEIBA_CONFIG)
        cursor = conn.cursor()
        
        # 日付を変換（2025-08-31 → 20250831）
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        kaisai_date = date_obj.strftime('%m%d')  # 0831形式
        kaisai_nen = date_obj.strftime('%Y')     # 2025形式
        
        # 競馬場コード取得
        keibajo_code = VENUE_MAPPING.get(venue)
        if not keibajo_code:
            logger.warning(f"未知の競馬場: {venue}")
            return {}
        
        # レース番号を2桁にフォーマット
        race_bango = f"{race_num:02d}"
        
        # 払い戻しデータ取得
        query = """
        SELECT 
            -- 単勝
            haraimodoshi_tansho_1a, haraimodoshi_tansho_1b,
            haraimodoshi_tansho_2a, haraimodoshi_tansho_2b,
            haraimodoshi_tansho_3a, haraimodoshi_tansho_3b,
            -- 複勝
            haraimodoshi_fukusho_1a, haraimodoshi_fukusho_1b,
            haraimodoshi_fukusho_2a, haraimodoshi_fukusho_2b,
            haraimodoshi_fukusho_3a, haraimodoshi_fukusho_3b,
            haraimodoshi_fukusho_4a, haraimodoshi_fukusho_4b,
            haraimodoshi_fukusho_5a, haraimodoshi_fukusho_5b,
            -- 馬連
            haraimodoshi_umaren_1a, haraimodoshi_umaren_1b,
            haraimodoshi_umaren_2a, haraimodoshi_umaren_2b,
            haraimodoshi_umaren_3a, haraimodoshi_umaren_3b,
            -- ワイド
            haraimodoshi_wide_1a, haraimodoshi_wide_1b,
            haraimodoshi_wide_2a, haraimodoshi_wide_2b,
            haraimodoshi_wide_3a, haraimodoshi_wide_3b,
            haraimodoshi_wide_4a, haraimodoshi_wide_4b,
            haraimodoshi_wide_5a, haraimodoshi_wide_5b,
            haraimodoshi_wide_6a, haraimodoshi_wide_6b,
            haraimodoshi_wide_7a, haraimodoshi_wide_7b,
            -- 馬単
            haraimodoshi_umatan_1a, haraimodoshi_umatan_1b,
            haraimodoshi_umatan_2a, haraimodoshi_umatan_2b,
            haraimodoshi_umatan_3a, haraimodoshi_umatan_3b,
            -- 三連複
            haraimodoshi_sanrenpuku_1a, haraimodoshi_sanrenpuku_1b,
            haraimodoshi_sanrenpuku_2a, haraimodoshi_sanrenpuku_2b,
            haraimodoshi_sanrenpuku_3a, haraimodoshi_sanrenpuku_3b,
            -- 三連単
            haraimodoshi_sanrentan_1a, haraimodoshi_sanrentan_1b,
            haraimodoshi_sanrentan_2a, haraimodoshi_sanrentan_2b,
            haraimodoshi_sanrentan_3a, haraimodoshi_sanrentan_3b
        FROM jvd_hr
        WHERE 
            kaisai_nen = %s AND
            kaisai_tsukihi = %s AND
            keibajo_code = %s AND
            race_bango = %s
        """
        
        cursor.execute(query, (kaisai_nen, kaisai_date, keibajo_code, race_bango))
        result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if not result:
            logger.info(f"データなし: {date_str} {venue} {race_num}R")
            return {}
        
        # 結果を整形
        payout_data = {
            '単勝_馬番': result[0] if result[0] and result[0].strip() else None,
            '単勝_払戻': int(result[1]) if result[1] and result[1].strip() else None,
            '複勝_馬番_1': result[6] if result[6] and result[6].strip() else None,
            '複勝_払戻_1': int(result[7]) if result[7] and result[7].strip() else None,
            '複勝_馬番_2': result[8] if result[8] and result[8].strip() else None,
            '複勝_払戻_2': int(result[9]) if result[9] and result[9].strip() else None,
            '複勝_馬番_3': result[10] if result[10] and result[10].strip() else None,
            '複勝_払戻_3': int(result[11]) if result[11] and result[11].strip() else None,
            '馬連_馬番': result[16] if result[16] and result[16].strip() else None,
            '馬連_払戻': int(result[17]) if result[17] and result[17].strip() else None,
            'ワイド_馬番_1': result[22] if result[22] and result[22].strip() else None,
            'ワイド_払戻_1': int(result[23]) if result[23] and result[23].strip() else None,
            'ワイド_馬番_2': result[24] if result[24] and result[24].strip() else None,
            'ワイド_払戻_2': int(result[25]) if result[25] and result[25].strip() else None,
            'ワイド_馬番_3': result[26] if result[26] and result[26].strip() else None,
            'ワイド_払戻_3': int(result[27]) if result[27] and result[27].strip() else None,
            '馬単_馬番': result[36] if result[36] and result[36].strip() else None,
            '馬単_払戻': int(result[37]) if result[37] and result[37].strip() else None,
            '三連複_馬番': result[42] if result[42] and result[42].strip() else None,
            '三連複_払戻': int(result[43]) if result[43] and result[43].strip() else None,
            '三連単_馬番': result[48] if result[48] and result[48].strip() else None,
            '三連単_払戻': int(result[49]) if result[49] and result[49].strip() else None
        }
        
        return payout_data
        
    except Exception as e:
        logger.error(f"pckeiba取得エラー: {e}")
        return {}

def save_payout_to_supabase(race_id: int, payout_data: Dict):
    """Supabaseに払い戻しデータを保存"""
    try:
        if not payout_data:
            return False
        
        # race_idを追加
        payout_data['race_id'] = race_id
        payout_data['取得日時'] = datetime.now().isoformat()
        
        # 既存データを削除
        supabase.table('jra_payouts').delete().eq('race_id', race_id).execute()
        
        # 新規データを挿入
        supabase.table('jra_payouts').insert(payout_data).execute()
        
        return True
        
    except Exception as e:
        logger.error(f"Supabase保存エラー: {e}")
        return False

def main():
    """メイン処理"""
    logger.info("=" * 60)
    logger.info("pckeiba払い戻しデータ取得開始")
    logger.info("=" * 60)
    
    # Supabaseから処理対象レースを取得
    try:
        races = supabase.table('jra_races').select('*').order('id').execute()
        total_races = len(races.data)
        logger.info(f"処理対象: {total_races}レース")
    except Exception as e:
        logger.error(f"レース情報取得エラー: {e}")
        return
    
    # 各レースの払い戻しデータを取得
    success_count = 0
    error_count = 0
    
    for i, race in enumerate(races.data, 1):
        race_id = race['id']
        race_date = race['開催日']
        venue = race['競馬場']
        race_num = race['レース番号']
        race_name = race.get('レース名', '')
        
        logger.info(f"[{i}/{total_races}] {race_date} {venue} {race_num}R {race_name}")
        
        # 払い戻しデータ取得
        payout_data = get_payout_from_pckeiba(race_date, venue, race_num)
        
        if payout_data and payout_data.get('単勝_馬番'):
            # Supabaseに保存
            if save_payout_to_supabase(race_id, payout_data):
                success_count += 1
                logger.info(f"  ✅ 保存完了 - 単勝: {payout_data['単勝_馬番']}番 {payout_data['単勝_払戻']}円")
            else:
                error_count += 1
                logger.warning(f"  ❌ 保存失敗")
        else:
            error_count += 1
            logger.warning(f"  ⚠️ データなし")
    
    # 結果サマリー
    logger.info("=" * 60)
    logger.info(f"処理完了: 成功 {success_count}件 / 失敗 {error_count}件")
    
    # 取得状況を確認
    result = supabase.table('jra_payouts').select('race_id').execute()
    logger.info(f"Supabase保存済み: {len(result.data)}件")

if __name__ == '__main__':
    main()