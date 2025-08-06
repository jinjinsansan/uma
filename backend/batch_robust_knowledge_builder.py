#!/usr/bin/env python3
"""
堅牢なD-Logic生データナレッジ構築バッチ（改良版）
MySQL接続タイムアウト対策・チャンク処理・自動復旧機能付き
"""
import os
import sys
import json
import time
import mysql.connector
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.dlogic_raw_data_manager import DLogicRawDataManager

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('batch_robust.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RobustKnowledgeBuilder:
    """堅牢なナレッジ構築システム"""
    
    def __init__(self):
        self.mysql_config = {
            'host': '172.25.160.1',
            'port': 3306,
            'user': 'root',
            'password': '04050405Aoi-',
            'database': 'mykeibadb',
            'charset': 'utf8mb4',
            'connect_timeout': 30,
            'autocommit': True
        }
        
        self.raw_manager = DLogicRawDataManager()
        self.connection = None
        self.processed_count = 0
        self.error_count = 0
        self.chunk_size = 100  # 小さなチャンクで処理
        self.reconnect_interval = 1000  # 1000頭ごとに接続リフレッシュ
        
        logger.info("🚀 堅牢なD-Logicナレッジ構築システム初期化")
    
    def get_fresh_connection(self) -> mysql.connector.MySQLConnection:
        """新しい接続を取得（タイムアウト対策）"""
        if self.connection:
            try:
                self.connection.close()
            except:
                pass
        
        max_retries = 5
        for attempt in range(max_retries):
            try:
                self.connection = mysql.connector.connect(**self.mysql_config)
                logger.info(f"✅ MySQL新規接続成功 (試行 {attempt + 1})")
                return self.connection
            except Exception as e:
                logger.warning(f"⚠️ MySQL接続失敗 (試行 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # 指数バックオフ
                else:
                    raise
        
        raise Exception("MySQL接続に失敗しました")
    
    def extract_horse_raw_data_robust(self, horse_name: str) -> Optional[Dict[str, Any]]:
        """堅牢な単一馬データ抽出"""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                # 接続チェック・再接続
                if not self.connection or not self.connection.is_connected():
                    self.get_fresh_connection()
                
                cursor = self.connection.cursor(dictionary=True)
                
                # レース履歴取得
                cursor.execute("""
                    SELECT 
                        u.RACE_CODE,
                        CONCAT(u.KAISAI_NEN, LPAD(u.KAISAI_GAPPI, 4, '0')) as date,
                        u.KAKUTEI_CHAKUJUN as finish,
                        u.TANSHO_ODDS as odds,
                        u.TANSHO_NINKIJUN as popularity,
                        u.FUTAN_JURYO as weight,
                        u.BATAIJU as horse_weight,
                        u.ZOGEN_SA as weight_change,
                        u.KISHUMEI_RYAKUSHO as jockey,
                        u.CHOKYOSHIMEI_RYAKUSHO as trainer,
                        u.CORNER1_JUNI,
                        u.CORNER2_JUNI,
                        u.CORNER3_JUNI,
                        u.CORNER4_JUNI,
                        u.SOHA_TIME as time,
                        u.BAREI as age,
                        u.SEIBETSU_CODE as sex,
                        r.KYORI as distance,
                        r.TRACK_CODE as track
                    FROM umagoto_race_joho u
                    LEFT JOIN race_shosai r ON u.RACE_CODE = r.RACE_CODE
                    WHERE u.BAMEI = %s
                    AND u.KAISAI_NEN >= 2020
                    ORDER BY u.KAISAI_NEN DESC, u.KAISAI_GAPPI DESC
                    LIMIT 50
                """, (horse_name,))
                
                races = cursor.fetchall()
                cursor.close()
                
                if not races:
                    return None
                
                # データ構造化
                race_history = []
                basic_info = {
                    "sex": races[0]['sex'] or "0",
                    "age": races[0]['age'] or 0,
                    "last_race_date": races[0]['date']
                }
                
                for race in races:
                    corner_positions = []
                    for corner in [race['CORNER1_JUNI'], race['CORNER2_JUNI'], 
                                 race['CORNER3_JUNI'], race['CORNER4_JUNI']]:
                        if corner and corner != 0:
                            corner_positions.append(int(corner))
                    
                    race_data = {
                        "race_code": race['RACE_CODE'],
                        "date": race['date'],
                        "finish": int(race['finish']) if race['finish'] else 0,
                        "odds": float(race['odds']) if race['odds'] else 0.0,
                        "popularity": int(race['popularity']) if race['popularity'] else 0,
                        "weight": int(race['weight']) if race['weight'] else 0,
                        "horse_weight": int(race['horse_weight']) if race['horse_weight'] else 0,
                        "weight_change": race['weight_change'] or "000",
                        "jockey": race['jockey'] or "",
                        "trainer": race['trainer'] or "",
                        "corner_positions": corner_positions,
                        "time": float(race['time']) if race['time'] else 0.0,
                        "age": int(race['age']) if race['age'] else 0,
                        "sex": race['sex'] or "0",
                        "distance": int(race['distance']) if race['distance'] else 0,
                        "track": race['track'] or ""
                    }
                    race_history.append(race_data)
                
                return {
                    "basic_info": basic_info,
                    "race_history": race_history
                }
                
            except Exception as e:
                logger.warning(f"⚠️ {horse_name} 抽出エラー (試行 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                    # 接続リフレッシュ
                    try:
                        self.get_fresh_connection()
                    except:
                        pass
                else:
                    return None
        
        return None
    
    def get_target_horses(self, exclude_existing=True) -> List[str]:
        """処理対象馬のリスト取得"""
        try:
            self.get_fresh_connection()
            cursor = self.connection.cursor()
            
            # 既存ナレッジから除外する馬名取得
            existing_horses = set()
            if exclude_existing:
                existing_data = self.raw_manager.knowledge_data
                existing_horses = set(existing_data.get('horses', {}).keys())
                logger.info(f"📚 既存ナレッジ: {len(existing_horses)}頭をスキップ")
            
            # ユニークな馬名を取得（2020年以降のデータ）
            cursor.execute("""
                SELECT DISTINCT u.BAMEI
                FROM umagoto_race_joho u
                WHERE u.KAISAI_NEN >= 2020
                AND u.BAMEI IS NOT NULL
                AND u.BAMEI != ''
                ORDER BY u.BAMEI
            """)
            
            all_horses = [row[0] for row in cursor.fetchall()]
            cursor.close()
            
            # 既存を除外
            target_horses = [horse for horse in all_horses if horse not in existing_horses]
            
            logger.info(f"🎯 処理対象: {len(target_horses)}頭（全体: {len(all_horses)}頭）")
            return target_horses
            
        except Exception as e:
            logger.error(f"❌ 対象馬取得エラー: {e}")
            return []
    
    def process_chunk(self, horses_chunk: List[str]) -> Dict[str, Any]:
        """チャンク単位での処理"""
        chunk_results = {}
        chunk_errors = 0
        
        for horse_name in horses_chunk:
            try:
                raw_data = self.extract_horse_raw_data_robust(horse_name)
                if raw_data:
                    chunk_results[horse_name] = raw_data
                    self.processed_count += 1
                else:
                    chunk_errors += 1
                    self.error_count += 1
                
                # プログレス表示
                if self.processed_count % 10 == 0:
                    logger.info(f"⏳ {self.processed_count}頭処理完了 (エラー: {self.error_count})")
                
            except Exception as e:
                logger.warning(f"❌ {horse_name} 処理エラー: {e}")
                chunk_errors += 1
                self.error_count += 1
        
        return chunk_results
    
    def run_robust_batch(self, max_horses: int = None):
        """堅牢なバッチ処理実行"""
        start_time = datetime.now()
        logger.info("🏗️ 堅牢なD-Logic生データナレッジ構築開始")
        
        # 処理対象馬取得
        target_horses = self.get_target_horses()
        if max_horses:
            target_horses = target_horses[:max_horses]
        
        if not target_horses:
            logger.info("✅ 処理対象馬がありません")
            return
        
        logger.info(f"🎯 処理予定: {len(target_horses)}頭")
        
        # チャンク単位で処理
        total_chunks = (len(target_horses) + self.chunk_size - 1) // self.chunk_size
        
        for i in range(0, len(target_horses), self.chunk_size):
            chunk_num = i // self.chunk_size + 1
            chunk_horses = target_horses[i:i + self.chunk_size]
            
            logger.info(f"📦 チャンク {chunk_num}/{total_chunks} 処理中 ({len(chunk_horses)}頭)")
            
            # 接続リフレッシュ
            if self.processed_count > 0 and self.processed_count % self.reconnect_interval == 0:
                logger.info("🔄 MySQL接続リフレッシュ")
                self.get_fresh_connection()
            
            # チャンク処理
            chunk_results = self.process_chunk(chunk_horses)
            
            # 中間保存
            if chunk_results:
                try:
                    for horse_name, horse_data in chunk_results.items():
                        self.raw_manager.add_horse_raw_data(horse_name, horse_data)
                    self.raw_manager._save_knowledge()
                    logger.info(f"💾 チャンク {chunk_num} 保存完了 ({len(chunk_results)}頭)")
                except Exception as e:
                    logger.error(f"❌ チャンク {chunk_num} 保存エラー: {e}")
            
            # 小休憩
            time.sleep(0.5)
        
        # 処理完了
        end_time = datetime.now()
        duration = end_time - start_time
        
        logger.info("✅ 堅牢なD-Logic生データナレッジ構築完了!")
        logger.info(f"📊 処理統計:")
        logger.info(f"  - 成功: {self.processed_count}頭")
        logger.info(f"  - エラー: {self.error_count}頭")
        logger.info(f"  - 処理時間: {duration}")
        
        # 最終確認
        final_data = self.raw_manager.knowledge_data
        total_horses = len(final_data.get('horses', {}))
        logger.info(f"📚 最終ナレッジ登録馬数: {total_horses}頭")

def main():
    """メイン処理"""
    builder = RobustKnowledgeBuilder()
    
    # 失敗した馬を優先して処理（最大5000頭）
    builder.run_robust_batch(max_horses=5000)

if __name__ == "__main__":
    main()