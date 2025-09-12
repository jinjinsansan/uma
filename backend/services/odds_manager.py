"""
オッズデータ管理モジュール
PostgreSQLデータベースとTSファイルからオッズを取得
"""
import logging
# import psycopg2  # Render環境では使用しない
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
        # Render環境ではPostgreSQLを使用しない
        logger.info(f"PostgreSQL無効（Render環境）: {kaisai_date} {jyocode} {race_number}R")
        return None
            

    
    def get_odds_from_ts_file(
        self,
        ts_file_path: str,
        race_identifier: str = None
    ) -> Optional[Dict[str, float]]:
        """
        TypeScriptファイルからオッズを取得
        
        Args:
            ts_file_path: TSファイルのパス
            race_identifier: レース識別子（レース番号）
        
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
            
            # レース番号が指定されている場合、該当レースを探す
            if race_identifier:
                # レース番号を含むセクションを探す (例: raceNumber: 11)
                race_num = str(race_identifier).replace('R', '')
                
                # raceNumber: 11 のようなパターンを探して、そのレースのoddsを取得
                pattern = rf'raceNumber:\s*{race_num}[,\s\}}].*?odds:\s*\[([\d.,\s]+)\]'
                match = re.search(pattern, content, re.DOTALL)
                
                if not match:
                    # 別のパターンを試す: race_number: 11 または "11R" を含むセクション
                    pattern = rf'"race_number":\s*{race_num}.*?odds:\s*\[([\d.,\s]+)\]'
                    match = re.search(pattern, content, re.DOTALL)
                
                if not match:
                    # さらに別のパターン: races配列の中から探す
                    # まずraces配列全体を取得
                    races_pattern = r'export const races[^=]*=\s*\[(.*?)\];'
                    races_match = re.search(races_pattern, content, re.DOTALL)
                    if races_match:
                        races_content = races_match.group(1)
                        # 各レースオブジェクトを分割（簡易的な方法）
                        race_objects = re.split(r'\},\s*\{', races_content)
                        
                        for i, race_obj in enumerate(race_objects):
                            # レース番号をチェック
                            race_num_match = re.search(rf'raceNumber:\s*{race_num}[,\s\}}]', race_obj)
                            if race_num_match:
                                # このレースのオッズを取得
                                odds_match = re.search(r'odds:\s*\[([\d.,\s]+)\]', race_obj)
                                if odds_match:
                                    odds_str = odds_match.group(1)
                                    odds_values = [float(x.strip()) for x in odds_str.split(',') if x.strip()]
                                    
                                    # 馬番 -> オッズのマッピングを作成
                                    odds_dict = {}
                                    for j, odds_value in enumerate(odds_values):
                                        horse_number = j + 1
                                        odds_dict[str(horse_number)] = odds_value
                                    
                                    # キャッシュに保存
                                    self.ts_odds_cache[cache_key] = odds_dict
                                    
                                    logger.info(f"TSファイルから{race_num}Rの{len(odds_dict)}頭のオッズを取得")
                                    return odds_dict
                
                if match:
                    odds_str = match.group(1)
                else:
                    logger.info(f"TSファイルに{race_num}Rのオッズデータなし")
                    return None
            else:
                # レース番号が指定されていない場合、最初のオッズを使用
                odds_pattern = r'odds:\s*\[([\d.,\s]+)\]'
                matches = re.findall(odds_pattern, content)
                
                if not matches:
                    logger.info(f"TSファイルにオッズデータなし: {ts_file_path}")
                    return None
                
                odds_str = matches[0]
            
            # オッズ値をパース
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
            import traceback
            traceback.print_exc()
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
                # フロントエンドのTSファイルパスを構築
                # 日付フォーマットを YYYYMMDD に変換
                date_str = today.replace('-', '')
                ts_filename = f"races-{date_str}-{venue}.ts"
                # フロントエンドのarchiveディレクトリを探す
                frontend_paths = [
                    f"/mnt/e/dev/Cusor/front/d-logic-ai-frontend/src/data/archive/{ts_filename}",
                    f"../front/d-logic-ai-frontend/src/data/archive/{ts_filename}",
                    f"../../front/d-logic-ai-frontend/src/data/archive/{ts_filename}"
                ]
                
                ts_path = None
                for path in frontend_paths:
                    if os.path.exists(path):
                        ts_path = path
                        logger.info(f"TSファイル発見: {path}")
                        break
                
                if ts_path and os.path.exists(ts_path):
                    logger.info(f"{race_number}Rのオッズを取得中...")
                    odds_dict = self.get_odds_from_ts_file(ts_path, race_number)
                    if odds_dict:
                        logger.info(f"取得成功: {len(odds_dict)}頭のオッズ")
                        # デバッグ: 最初の3頭のオッズを表示
                        for i, (num, odds) in enumerate(list(odds_dict.items())[:3]):
                            logger.info(f"  馬番{num}: {odds}倍")
                    else:
                        logger.warning(f"{race_number}Rのオッズ取得失敗")
            
            # 3. 馬名にマッピング（馬名リストがある場合）
            if odds_dict and horses:
                return self.get_odds_with_horse_names(odds_dict, horses)
            
            # 4. オッズデータがない場合はNoneを返す
            if not odds_dict and horses:
                logger.warning("オッズデータが取得できません")
                return None
            
            return odds_dict or {}
            
        except Exception as e:
            logger.error(f"リアルタイムオッズ取得エラー: {e}")
            return None  # エラー時もNoneを返す
    
    def close(self):
        """データベース接続をクローズ"""
        # Render環境ではDB接続なし
        pass
    
    def __del__(self):
        """デストラクタ"""
        self.close()

# グローバルインスタンス
odds_manager = OddsManager()