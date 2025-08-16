import os
import pymysql
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import logging

# ロガー設定
logger = logging.getLogger(__name__)

router = APIRouter()

# MySQL設定（環境変数から取得、デフォルト値設定）
MYSQL_CONFIG = {
    'host': os.getenv('MYSQL_HOST', '172.25.160.1'),
    'port': int(os.getenv('MYSQL_PORT', 3306)),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', 'admin'),
    'database': os.getenv('MYSQL_DATABASE', 'mykeibadb'),
    'charset': 'utf8mb4'
}

def get_tomorrow_races() -> List[Dict[str, Any]]:
    """明日のレース情報を取得"""
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    tomorrow_formatted = (datetime.now() + timedelta(days=1)).strftime('%Y%m%d')
    
    try:
        connection = pymysql.connect(**MYSQL_CONFIG)
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # 明日のレース情報を取得（umagoto_race_johoテーブルから）
        query = """
        SELECT DISTINCT
            CONCAT(KEIBAJO_NAME, '_', RACE_BANGO) as race_id,
            KAISAI_BI as race_date,
            KEIBAJO_NAME as venue,
            RACE_BANGO as race_number,
            KYOSOMEI_HONDAI as race_name,
            KYORI as distance,
            JOKEN as class_info,
            HASSOJIKOKU as start_time
        FROM umagoto_race_joho 
        WHERE KAISAI_BI = %s
        GROUP BY KEIBAJO_NAME, RACE_BANGO
        ORDER BY KEIBAJO_NAME, RACE_BANGO
        """
        
        cursor.execute(query, (tomorrow,))
        races = cursor.fetchall()
        
        # 各レースの出走馬情報を取得
        formatted_races = []
        for race in races:
            # 出走馬を取得
            horse_query = """
            SELECT DISTINCT
                BAMEI as horse_name,
                KISHUMEI as jockey_name,
                CHOKYOSHIMEI as trainer_name,
                BATAIJU as weight,
                WAKUBAN as post_position
            FROM umagoto_race_joho
            WHERE KAISAI_BI = %s 
              AND KEIBAJO_NAME = %s 
              AND RACE_BANGO = %s
            ORDER BY WAKUBAN, UMABAN
            """
            
            cursor.execute(horse_query, (tomorrow, race['venue'], race['race_number']))
            horses_data = cursor.fetchall()
            horses = [horse['horse_name'] for horse in horses_data if horse['horse_name']]
            
            # 開催場名を統一フォーマットに変換
            venue_map = {
                '東京': '東京',
                '中山': '中山',
                '阪神': '阪神',
                '京都': '京都',
                '中京': '中京',
                '新潟': '新潟',
                '札幌': '札幌',
                '函館': '函館',
                '福島': '福島',
                '小倉': '小倉'
            }
            
            venue_name = race['venue']
            for key, value in venue_map.items():
                if key in venue_name:
                    venue_name = value
                    break
            
            # レース名とクラス情報を組み合わせて整形
            race_name = race['race_name'] or f"{race['race_number']}R"
            if race['class_info']:
                race_name = f"{race_name} [{race['class_info']}]"
            if race['start_time']:
                race_name = f"{race_name} ({race['start_time']}発走)"
            
            formatted_race = {
                'race_id': f"jvlink-{venue_name.lower()}-{race['race_number']}r-{tomorrow_formatted}",
                'race_date': tomorrow,
                'venue': venue_name,
                'race_number': race['race_number'],
                'race_name': race_name,
                'horses': horses,
                'created_at': datetime.now().isoformat()
            }
            
            if horses:  # 出走馬がいる場合のみ追加
                formatted_races.append(formatted_race)
        
        return formatted_races
        
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()

@router.get("/tomorrow")
async def get_tomorrow_race_data():
    """明日のレース情報を取得するAPI"""
    try:
        races = get_tomorrow_races()
        
        return {
            'success': True,
            'date': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
            'races': races,
            'total': len(races),
            'source': 'mykeibadb'
        }
        
    except Exception as e:
        logger.error(f"Error fetching tomorrow's races: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'races': [],
            'message': 'JV-Linkデータの取得に失敗しました。mykeibadb.exeが起動していることを確認してください。'
        }

@router.get("/check-database")
async def check_database_connection():
    """データベース接続状態を確認"""
    try:
        connection = pymysql.connect(**MYSQL_CONFIG)
        cursor = connection.cursor()
        
        # テーブル存在確認
        cursor.execute("SHOW TABLES LIKE 'umagoto_race_joho'")
        table_exists = cursor.fetchone() is not None
        
        # レコード数確認
        count = 0
        if table_exists:
            cursor.execute("SELECT COUNT(*) FROM umagoto_race_joho")
            count = cursor.fetchone()[0]
        
        cursor.close()
        connection.close()
        
        return {
            'connected': True,
            'table_exists': table_exists,
            'record_count': count,
            'database': MYSQL_CONFIG['database'],
            'host': MYSQL_CONFIG['host']
        }
        
    except Exception as e:
        return {
            'connected': False,
            'error': str(e),
            'message': 'MySQLデータベースに接続できません'
        }