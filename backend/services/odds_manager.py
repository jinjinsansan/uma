"""
オッズデータ管理モジュール
PostgreSQLデータベースとTSファイルからオッズを取得
"""
import logging
import psycopg2
import json
import re
import os
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class OddsManager:
    """オッズデータ管理クラス"""
    
    # PostgreSQL接続設定（ローカル環境）
    PG_CONNECTION = {
        "host": "172.25.160.1",  # WSL2からWindowsのPostgreSQL
        "port": "5432",
        "database": "pckeiba",
        "user": "postgres",
        "password": "postgres"
    }
    
    def __init__(self):
        """初期化"""
        self.conn = None
        self.ts_odds_cache = {}  # TSファイルのオッズキャッシュ
        logger.info("オッズデータマネージャーを初期化しました")
    
    def get_odds_from_database(
        self,
        kaisai_date: str,
        jyocode: str,
        race_number: int
    ) -> Optional[Dict[str, float]]:
        """
        PostgreSQLデータベースからオッズを取得
        
        Args:
            kaisai_date: 開催日（YYYY-MM-DD形式）
            jyocode: 競馬場コード（例: '09'は阪神）
            race_number: レース番号
        
        Returns:
            馬番 -> オッズのマッピング、取得失敗時はNone
        """
        try:
            # 日付を変換（YYYY-MM-DD -> YYYYMMDD）
            date_parts = kaisai_date.split('-')
            if len(date_parts) == 3:
                kaisai_nen = date_parts[0]
                kaisai_tsukihi = date_parts[1] + date_parts[2]
            else:
                logger.error(f"不正な日付形式: {kaisai_date}")
                return None
            
            # データベース接続
            if not self.conn or self.conn.closed:
                self.conn = psycopg2.connect(**self.PG_CONNECTION)
            
            cur = self.conn.cursor()
            
            # jvd_o1テーブルから単勝オッズを取得
            query = """
                SELECT 
                    race_bango,
                    shusso_tosu,
                    odds_tansho
                FROM jvd_o1
                WHERE kaisai_nen = %s
                AND kaisai_tsukihi = %s
                AND keibajo_code = %s
                AND race_bango = %s
            """
            
            race_bango = f"{race_number:02d}"
            cur.execute(query, (kaisai_nen, kaisai_tsukihi, jyocode, race_bango))
            
            result = cur.fetchone()
            if not result:
                logger.info(f"データベースにオッズデータなし: {kaisai_date} {jyocode} {race_number}R")
                return None
            
            race_no, tosu, tansho_str = result
            
            if not tansho_str:
                logger.info(f"オッズ文字列が空: {kaisai_date} {jyocode} {race_number}R")
                return None
            
            # オッズ文字列をパース（6桁固定長フォーマット）
            odds_dict = {}
            odds_per_horse = 6
            num_horses = len(tansho_str) // odds_per_horse
            
            for i in range(num_horses):
                start = i * odds_per_horse
                end = start + odds_per_horse
                odds_raw = tansho_str[start:end]
                
                try:
                    # オッズは10倍して格納されている
                    odds_value = float(odds_raw) / 10.0
                    # 馬番は1から始まる
                    horse_number = i + 1
                    odds_dict[str(horse_number)] = odds_value
                except Exception as e:
                    logger.warning(f"オッズパースエラー（{i+1}番馬）: {odds_raw}")
                    continue
            
            logger.info(f"データベースから{len(odds_dict)}頭のオッズを取得: {kaisai_date} {jyocode} {race_number}R")
            return odds_dict
            
        except Exception as e:
            logger.error(f"データベースからのオッズ取得エラー: {e}")
            return None
        finally:
            if cur:
                cur.close()
    
    def get_odds_from_ts_file(
        self,
        ts_file_path: str,
        race_identifier: str = None
    ) -> Optional[Dict[str, float]]:
        """
        TypeScriptファイルからオッズを取得
        
        Args:
            ts_file_path: TSファイルのパス
            race_identifier: レース識別子（オプション）
        
        Returns:
            馬番または馬名 -> オッズのマッピング
        """
        try:
            if not os.path.exists(ts_file_path):
                logger.error(f"TSファイルが存在しません: {ts_file_path}")
                return None
            
            # キャッシュチェック
            cache_key = f"{ts_file_path}_{race_identifier}"
            if cache_key in self.ts_odds_cache:
                return self.ts_odds_cache[cache_key]
            
            with open(ts_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # オッズ配列を探す（odds: [数値, 数値, ...]）
            odds_pattern = r'odds:\s*\[([\d.,\s]+)\]'
            matches = re.findall(odds_pattern, content)
            
            if not matches:
                logger.info(f"TSファイルにオッズデータなし: {ts_file_path}")
                return None
            
            # 最初のマッチを使用（複数レースの場合は race_identifier で特定）
            odds_str = matches[0]
            odds_values = [float(x.strip()) for x in odds_str.split(',') if x.strip()]
            
            # 馬番 -> オッズのマッピングを作成
            odds_dict = {}
            for i, odds_value in enumerate(odds_values):
                horse_number = i + 1
                odds_dict[str(horse_number)] = odds_value
            
            # キャッシュに保存
            self.ts_odds_cache[cache_key] = odds_dict
            
            logger.info(f"TSファイルから{len(odds_dict)}頭のオッズを取得: {ts_file_path}")
            return odds_dict
            
        except Exception as e:
            logger.error(f"TSファイルからのオッズ取得エラー: {e}")
            return None
    
    def get_odds_with_horse_names(
        self,
        odds_dict: Dict[str, float],
        horses: List[str]
    ) -> Dict[str, float]:
        """
        馬番のオッズを馬名にマッピング
        
        Args:
            odds_dict: 馬番 -> オッズのマッピング
            horses: 馬名リスト（馬番順）
        
        Returns:
            馬名 -> オッズのマッピング
        """
        if not odds_dict or not horses:
            return {}
        
        result = {}
        for i, horse_name in enumerate(horses):
            horse_number = str(i + 1)
            if horse_number in odds_dict:
                result[horse_name] = odds_dict[horse_number]
        
        return result
    
    def get_real_time_odds(
        self,
        venue: str,
        race_number: int,
        horses: List[str] = None
    ) -> Dict[str, float]:
        """
        リアルタイムオッズを取得（優先順位: DB -> TSファイル -> デフォルト）
        
        Args:
            venue: 開催場
            race_number: レース番号
            horses: 馬名リスト（オプション）
        
        Returns:
            馬名または馬番 -> オッズのマッピング
        """
        try:
            # 今日の日付を取得
            today = datetime.now().strftime("%Y-%m-%d")
            
            # 開催場コード変換
            venue_code_map = {
                '東京': '11', '中山': '12', '京都': '13', '阪神': '14',
                '中京': '15', '新潟': '16', '札幌': '17', '函館': '18',
                '福島': '19', '小倉': '20'
            }
            jyocode = venue_code_map.get(venue, '00')
            
            # 1. データベースから取得を試みる
            odds_dict = self.get_odds_from_database(today, jyocode, race_number)
            
            # 2. TSファイルから取得を試みる（DBになかった場合）
            if not odds_dict:
                # TSファイルのパスを構築（例: predictions/2025-09-13_阪神_11R.ts）
                ts_filename = f"{today}_{venue}_{race_number}R.ts"
                ts_path = os.path.join("predictions", ts_filename)
                
                if os.path.exists(ts_path):
                    odds_dict = self.get_odds_from_ts_file(ts_path)
            
            # 3. 馬名にマッピング（馬名リストがある場合）
            if odds_dict and horses:
                return self.get_odds_with_horse_names(odds_dict, horses)
            
            # 4. デフォルト値を返す（オッズが取得できなかった場合）
            if not odds_dict and horses:
                logger.info("オッズデータが取得できないため、デフォルト値を使用")
                return {horse: 10.0 for horse in horses}  # デフォルトオッズ10倍
            
            return odds_dict or {}
            
        except Exception as e:
            logger.error(f"リアルタイムオッズ取得エラー: {e}")
            if horses:
                return {horse: 10.0 for horse in horses}
            return {}
    
    def close(self):
        """データベース接続をクローズ"""
        if self.conn and not self.conn.closed:
            self.conn.close()
            logger.info("データベース接続をクローズしました")
    
    def __del__(self):
        """デストラクタ"""
        self.close()

# グローバルインスタンス
odds_manager = OddsManager()