#!/usr/bin/env python3
"""
pckeiba PostgreSQLから払い戻し結果を取得してSupabaseに保存
"""

import os
import sys
import psycopg2
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
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
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

# pckeiba PostgreSQL設定
PCKEIBA_CONFIG = {
    'host': os.getenv('PCKEIBA_HOST', 'localhost'),
    'port': os.getenv('PCKEIBA_PORT', 5432),
    'database': os.getenv('PCKEIBA_DB', 'pckeiba'),
    'user': os.getenv('PCKEIBA_USER', 'postgres'),
    'password': os.getenv('PCKEIBA_PASSWORD', '')
}

# Supabaseクライアント初期化
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# 競馬場名のマッピング
VENUE_MAPPING = {
    '中山': '06',
    '阪神': '09',
    '札幌': '01',
    '新潟': '04',
    '中京': '07'
}

class PckeibaFetcher:
    """pckeiba PostgreSQLから払い戻しデータを取得"""
    
    def __init__(self):
        self.connection = None
        self.cursor = None
    
    def connect(self):
        """PostgreSQLに接続"""
        try:
            self.connection = psycopg2.connect(**PCKEIBA_CONFIG)
            self.cursor = self.connection.cursor()
            logger.info("pckeiba PostgreSQL接続成功")
            return True
        except Exception as e:
            logger.error(f"pckeiba接続エラー: {e}")
            return False
    
    def disconnect(self):
        """接続を閉じる"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
    
    def get_payout_data(self, race_date: str, venue: str, race_num: int) -> Dict:
        """
        特定レースの払い戻しデータを取得
        
        Args:
            race_date: 開催日 (YYYY-MM-DD形式)
            venue: 競馬場名
            race_num: レース番号
            
        Returns:
            払い戻しデータの辞書
        """
        try:
            # 日付を変換
            date_obj = datetime.strptime(race_date, '%Y-%m-%d')
            year = date_obj.year
            month = date_obj.month
            day = date_obj.day
            
            # 競馬場コード取得
            venue_code = VENUE_MAPPING.get(venue)
            if not venue_code:
                logger.warning(f"未知の競馬場: {venue}")
                return {}
            
            # SQLクエリ（pckeiba用に調整が必要）
            # 以下は仮のテーブル構造です。実際のpckeibaのテーブル構造に合わせて修正が必要
            query = """
            SELECT 
                単勝_馬番, 単勝_払戻,
                複勝_馬番_1, 複勝_払戻_1,
                複勝_馬番_2, 複勝_払戻_2,
                複勝_馬番_3, 複勝_払戻_3,
                馬連_馬番, 馬連_払戻,
                ワイド_馬番_1, ワイド_払戻_1,
                ワイド_馬番_2, ワイド_払戻_2,
                ワイド_馬番_3, ワイド_払戻_3,
                馬単_馬番, 馬単_払戻,
                三連複_馬番, 三連複_払戻,
                三連単_馬番, 三連単_払戻
            FROM payouts
            WHERE 
                開催年 = %s AND 
                開催月 = %s AND 
                開催日 = %s AND
                競馬場コード = %s AND
                レース番号 = %s
            """
            
            self.cursor.execute(query, (year, month, day, venue_code, race_num))
            result = self.cursor.fetchone()
            
            if not result:
                logger.info(f"払い戻しデータなし: {race_date} {venue} {race_num}R")
                return {}
            
            # 結果を辞書に整形
            payout_data = {
                '単勝': {
                    '馬番': result[0],
                    '払戻': result[1]
                },
                '複勝': [
                    {'馬番': result[2], '払戻': result[3]},
                    {'馬番': result[4], '払戻': result[5]},
                    {'馬番': result[6], '払戻': result[7]}
                ],
                '馬連': {
                    '馬番': result[8],
                    '払戻': result[9]
                },
                'ワイド': [
                    {'馬番': result[10], '払戻': result[11]},
                    {'馬番': result[12], '払戻': result[13]},
                    {'馬番': result[14], '払戻': result[15]}
                ],
                '馬単': {
                    '馬番': result[16],
                    '払戻': result[17]
                },
                '三連複': {
                    '馬番': result[18],
                    '払戻': result[19]
                },
                '三連単': {
                    '馬番': result[20],
                    '払戻': result[21]
                }
            }
            
            return payout_data
            
        except Exception as e:
            logger.error(f"払い戻しデータ取得エラー: {e}")
            return {}

def save_to_supabase(race_id: int, payout_data: Dict):
    """Supabaseに払い戻しデータを保存"""
    try:
        if not payout_data:
            return
        
        # jra_payoutsテーブルへの保存
        data = {
            'race_id': race_id,
            '単勝_馬番': payout_data.get('単勝', {}).get('馬番'),
            '単勝_払戻': payout_data.get('単勝', {}).get('払戻'),
            '複勝_馬番_1': payout_data.get('複勝', [{}])[0].get('馬番'),
            '複勝_払戻_1': payout_data.get('複勝', [{}])[0].get('払戻'),
            '複勝_馬番_2': payout_data.get('複勝', [{}, {}])[1].get('馬番'),
            '複勝_払戻_2': payout_data.get('複勝', [{}, {}])[1].get('払戻'),
            '複勝_馬番_3': payout_data.get('複勝', [{}, {}, {}])[2].get('馬番'),
            '複勝_払戻_3': payout_data.get('複勝', [{}, {}, {}])[2].get('払戻'),
            '馬連_馬番': payout_data.get('馬連', {}).get('馬番'),
            '馬連_払戻': payout_data.get('馬連', {}).get('払戻'),
            'ワイド_馬番_1': payout_data.get('ワイド', [{}])[0].get('馬番'),
            'ワイド_払戻_1': payout_data.get('ワイド', [{}])[0].get('払戻'),
            'ワイド_馬番_2': payout_data.get('ワイド', [{}, {}])[1].get('馬番'),
            'ワイド_払戻_2': payout_data.get('ワイド', [{}, {}])[1].get('払戻'),
            'ワイド_馬番_3': payout_data.get('ワイド', [{}, {}, {}])[2].get('馬番'),
            'ワイド_払戻_3': payout_data.get('ワイド', [{}, {}, {}])[2].get('払戻'),
            '馬単_馬番': payout_data.get('馬単', {}).get('馬番'),
            '馬単_払戻': payout_data.get('馬単', {}).get('払戻'),
            '三連複_馬番': payout_data.get('三連複', {}).get('馬番'),
            '三連複_払戻': payout_data.get('三連複', {}).get('払戻'),
            '三連単_馬番': payout_data.get('三連単', {}).get('馬番'),
            '三連単_払戻': payout_data.get('三連単', {}).get('払戻'),
            '取得日時': datetime.now().isoformat()
        }
        
        # 既存データを削除
        supabase.table('jra_payouts').delete().eq('race_id', race_id).execute()
        
        # 新規データを挿入
        supabase.table('jra_payouts').insert(data).execute()
        
        logger.info(f"払い戻しデータ保存完了: race_id={race_id}")
        
    except Exception as e:
        logger.error(f"Supabase保存エラー: {e}")

def main():
    """メイン処理"""
    logger.info("=" * 60)
    logger.info("pckeiba払い戻しデータ取得開始")
    logger.info("=" * 60)
    
    # Supabaseから処理対象レースを取得
    try:
        races = supabase.table('jra_races').select('*').execute()
        total_races = len(races.data)
        logger.info(f"処理対象: {total_races}レース")
    except Exception as e:
        logger.error(f"レース情報取得エラー: {e}")
        return
    
    # pckeiba接続
    fetcher = PckeibaFetcher()
    if not fetcher.connect():
        logger.error("pckeiba接続失敗")
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
        payout_data = fetcher.get_payout_data(race_date, venue, race_num)
        
        if payout_data:
            # Supabaseに保存
            save_to_supabase(race_id, payout_data)
            success_count += 1
        else:
            logger.warning(f"  データ取得失敗またはデータなし")
            error_count += 1
    
    # 接続を閉じる
    fetcher.disconnect()
    
    # 結果サマリー
    logger.info("=" * 60)
    logger.info(f"処理完了: 成功 {success_count}件 / 失敗 {error_count}件")
    
    # 取得状況を確認
    result = supabase.table('jra_payouts').select('race_id').execute()
    logger.info(f"Supabase保存済み: {len(result.data)}件")

if __name__ == '__main__':
    main()