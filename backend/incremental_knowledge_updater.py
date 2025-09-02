#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全ナレッジファイル統合差分更新システム
対象ファイル:
1. dlogic_raw_knowledge.json - D-Logic標準ナレッジ
2. dlogic_extended_knowledge.json - I-Logic/IM拡張ナレッジ  
3. jockey_knowledge.json - 騎手ナレッジ
4. viewlogic_knowledge.json - ViewLogicナレッジ
"""

import json
import os
import mysql.connector
from datetime import datetime, timedelta
import logging
from collections import defaultdict
import time

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('incremental_update.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class IncrementalKnowledgeUpdater:
    """全ナレッジファイル統合差分更新クラス - MySQL生データコピー方式"""
    
    def __init__(self):
        self.connection = None
        self.file_creation_dates = {
            'dlogic_raw_knowledge.json': '2025-08-09',
            'dlogic_extended_knowledge.json': '2025-08-19', 
            'jockey_knowledge.json': '2025-08-17',
            'viewlogic_knowledge.json': '2025-08-03'
        }
        
    def connect_db(self):
        """データベース接続"""
        try:
            self.connection = mysql.connector.connect(
                host='172.25.160.1',
                user='root',
                password='04050405Aoi-',
                database='mykeibadb',
                charset='utf8mb4',
                collation='utf8mb4_general_ci'
            )
            logging.info("データベース接続成功")
            return True
        except Exception as e:
            logging.error(f"データベース接続エラー: {e}")
            return False
    
    def get_new_horses_since_date(self, since_date):
        """指定日以降に出走した新しい馬のリストを取得"""
        cursor = self.connection.cursor()
        
        query = """
        SELECT DISTINCT u.BAMEI
        FROM umagoto_race_joho u
        WHERE u.KAISAI_NEN >= %s
        AND u.KAISAI_GAPPI >= %s
        AND u.BAMEI IS NOT NULL 
        AND u.BAMEI != ''
        ORDER BY u.BAMEI
        """
        
        year = since_date[:4]
        month_day = since_date[5:].replace('-', '')
        
        try:
            cursor.execute(query, (year, month_day))
            horses = [row[0] for row in cursor.fetchall()]
            logging.info(f"{since_date}以降の出走馬: {len(horses)}頭")
            return horses
            
        except Exception as e:
            logging.error(f"新馬リスト取得エラー: {e}")
            return []
        finally:
            cursor.close()
    
    def get_new_jockeys_since_date(self, since_date):
        """指定日以降に騎乗した騎手のリストを取得"""
        cursor = self.connection.cursor()
        
        query = """
        SELECT DISTINCT u.KISHUMEI_RYAKUSHO
        FROM umagoto_race_joho u
        WHERE u.KAISAI_NEN >= %s
        AND u.KAISAI_GAPPI >= %s
        AND u.KISHUMEI_RYAKUSHO IS NOT NULL 
        AND u.KISHUMEI_RYAKUSHO != ''
        ORDER BY u.KISHUMEI_RYAKUSHO
        """
        
        year = since_date[:4]
        month_day = since_date[5:].replace('-', '')
        
        try:
            cursor.execute(query, (year, month_day))
            jockeys = [row[0] for row in cursor.fetchall()]
            logging.info(f"{since_date}以降の騎乗騎手: {len(jockeys)}名")
            return jockeys
            
        except Exception as e:
            logging.error(f"騎手リスト取得エラー: {e}")
            return []
        finally:
            cursor.close()
    
    def get_new_races_since_date(self, since_date):
        """指定日以降の重要レース情報を取得"""
        cursor = self.connection.cursor()
        
        query = """
        SELECT DISTINCT r.RACE_MEI, r.GRADE_CODE, r.KYORI,
               r.KEIBAJO_CODE, r.KAISAI_NEN, r.KAISAI_GAPPI,
               r.RACE_CODE
        FROM race_shosai r
        WHERE r.KAISAI_NEN >= %s
        AND r.KAISAI_GAPPI >= %s
        AND r.GRADE_CODE IN ('1', '2', '3', 'L')
        ORDER BY r.KAISAI_NEN, r.KAISAI_GAPPI
        """
        
        year = since_date[:4]
        month_day = since_date[5:].replace('-', '')
        
        try:
            cursor.execute(query, (year, month_day))
            races = []
            for row in cursor.fetchall():
                race_info = {
                    'race_name': row[0],
                    'grade_code': row[1],
                    'distance': row[2],
                    'venue_code': row[3],
                    'year': row[4],
                    'date': row[5],
                    'race_code': row[6]
                }
                races.append(race_info)
            
            logging.info(f"{since_date}以降の重要レース: {len(races)}レース")
            return races
            
        except Exception as e:
            logging.error(f"重要レース取得エラー: {e}")
            return []
        finally:
            cursor.close()
    
    def get_horse_race_data(self, horse_name):
        """指定馬の全過去レース成績を取得（MySQL生データ）"""
        cursor = self.connection.cursor()
        
        query = """
        SELECT u.KAISAI_NEN, u.KAISAI_GAPPI, u.RACE_CODE,
               u.KAKUTEI_CHAKUJUN, u.NYUSEN_JUNI, u.WAKUBAN, u.UMABAN,
               r.RACE_MEI, r.KYORI, r.KEIBAJO_CODE, r.TRACK_CODE,
               u.KISHUMEI_RYAKUSHO, u.KINRYO, k.KETTO1_BAMEI,
               u.TANSHO_ODDS, u.FUKUSHO_ODDS, u.TIME_RECORD
        FROM umagoto_race_joho u
        LEFT JOIN race_shosai r ON u.RACE_CODE = r.RACE_CODE
        LEFT JOIN kyosoba_master2 k ON u.KETTO_TOROKU_BANGO = k.KETTO_TOROKU_BANGO
        WHERE u.BAMEI = %s
        ORDER BY u.KAISAI_NEN DESC, u.KAISAI_GAPPI DESC
        """
        
        try:
            cursor.execute(query, (horse_name,))
            race_records = []
            
            for row in cursor.fetchall():
                race_data = {
                    'year': row[0],
                    'date': row[1],
                    'race_code': row[2],
                    'finish_position': row[3],
                    'total_horses': row[4],
                    'gate_number': row[5],
                    'horse_number': row[6],
                    'race_name': row[7],
                    'distance': row[8],
                    'venue_code': row[9],
                    'track_condition': row[10],
                    'jockey': row[11],
                    'weight': row[12],
                    'sire': row[13],
                    'win_odds': row[14],
                    'place_odds': row[15],
                    'time_record': row[16]
                }
                race_records.append(race_data)
            
            return {
                'horse_name': horse_name,
                'race_records': race_records,
                'total_races': len(race_records)
            }
            
        except Exception as e:
            logging.error(f"馬データ取得エラー({horse_name}): {e}")
            return None
        finally:
            cursor.close()
    
    def get_jockey_race_data(self, jockey_name):
        """指定騎手の成績データを取得（MySQL生データ）"""
        cursor = self.connection.cursor()
        
        query = """
        SELECT u.KAISAI_NEN, u.KAISAI_GAPPI, u.BAMEI,
               u.KAKUTEI_CHAKUJUN, u.NYUSEN_JUNI, u.WAKUBAN,
               r.RACE_MEI, r.KYORI, r.KEIBAJO_CODE, r.TRACK_CODE,
               k.KETTO1_BAMEI
        FROM umagoto_race_joho u
        LEFT JOIN race_shosai r ON u.RACE_CODE = r.RACE_CODE
        LEFT JOIN kyosoba_master2 k ON u.KETTO_TOROKU_BANGO = k.KETTO_TOROKU_BANGO
        WHERE u.KISHUMEI_RYAKUSHO = %s
        AND u.KAISAI_NEN >= '2015'
        ORDER BY u.KAISAI_NEN DESC, u.KAISAI_GAPPI DESC
        """
        
        try:
            cursor.execute(query, (jockey_name,))
            race_records = []
            
            for row in cursor.fetchall():
                race_data = {
                    'year': row[0],
                    'date': row[1],
                    'horse_name': row[2],
                    'finish_position': row[3],
                    'total_horses': row[4],
                    'gate_number': row[5],
                    'race_name': row[6],
                    'distance': row[7],
                    'venue_code': row[8],
                    'track_condition': row[9],
                    'sire': row[10]
                }
                race_records.append(race_data)
            
            return {
                'jockey_name': jockey_name,
                'race_records': race_records,
                'total_races': len(race_records)
            }
            
        except Exception as e:
            logging.error(f"騎手データ取得エラー({jockey_name}): {e}")
            return None
        finally:
            cursor.close()
    
    def update_dlogic_raw_knowledge(self, new_horses):
        """D-Logic標準ナレッジに新馬データを追加"""
        filepath = 'data/dlogic_raw_knowledge.json'
        
        # 既存ファイル読み込み
        with open(filepath, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
        
        updated_count = 0
        
        for horse_name in new_horses:
            if horse_name not in existing_data:
                # MySQLから馬の全レース成績を取得
                horse_data = self.get_horse_race_data(horse_name)
                if horse_data and horse_data['total_races'] >= 3:  # 3レース以上の馬のみ
                    existing_data[horse_name] = horse_data
                    updated_count += 1
                    logging.info(f"追加: {horse_name} ({horse_data['total_races']}レース)")
        
        # ファイル保存
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=2)
        
        logging.info(f"D-Logic標準ナレッジ更新完了: {updated_count}頭追加")
        return updated_count
    
    def update_dlogic_extended_knowledge(self, new_horses):
        """拡張ナレッジに新馬データを追加"""
        filepath = 'data/dlogic_extended_knowledge.json'
        
        with open(filepath, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
        
        updated_count = 0
        
        for horse_name in new_horses:
            if horse_name not in existing_data:
                horse_data = self.get_horse_race_data(horse_name)
                if horse_data:
                    existing_data[horse_name] = horse_data
                    updated_count += 1
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=2)
        
        logging.info(f"拡張ナレッジ更新完了: {updated_count}頭追加")
        return updated_count
    
    def update_jockey_knowledge(self, new_jockeys):
        """騎手ナレッジに新騎手データを追加"""
        filepath = 'data/jockey_knowledge.json'
        
        with open(filepath, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
        
        updated_count = 0
        
        for jockey_name in new_jockeys:
            if jockey_name not in existing_data:
                jockey_data = self.get_jockey_race_data(jockey_name)
                if jockey_data:
                    existing_data[jockey_name] = jockey_data
                    updated_count += 1
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=2)
        
        logging.info(f"騎手ナレッジ更新完了: {updated_count}名追加")
        return updated_count
    
    def update_viewlogic_knowledge(self, new_races):
        """ViewLogicナレッジに新レースデータを追加"""
        filepath = 'data/viewlogic_knowledge.json'
        
        with open(filepath, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
        
        updated_count = 0
        
        for race_info in new_races:
            race_key = f"{race_info['race_name']}_{race_info['year']}"
            if race_key not in existing_data:
                # レースの出走馬リストを取得
                race_horses = self.get_race_horses_list(race_info['race_code'])
                
                race_data = {
                    'race_name': race_info['race_name'],
                    'grade': race_info['grade_code'],
                    'distance': race_info['distance'],
                    'venue': race_info['venue_code'],
                    'date': f"{race_info['year']}-{race_info['date']}",
                    'horses': race_horses
                }
                
                existing_data[race_key] = race_data
                updated_count += 1
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=2)
        
        logging.info(f"ViewLogicナレッジ更新完了: {updated_count}レース追加")
        return updated_count
    
    def get_race_horses_list(self, race_code):
        """指定レースの出走馬リストを取得"""
        cursor = self.connection.cursor()
        
        query = """
        SELECT DISTINCT BAMEI
        FROM umagoto_race_joho
        WHERE RACE_CODE = %s
        ORDER BY UMABAN
        """
        
        try:
            cursor.execute(query, (race_code,))
            horses = [row[0] for row in cursor.fetchall()]
            return horses
            
        except Exception as e:
            logging.error(f"レース出走馬取得エラー({race_code}): {e}")
            return []
        finally:
            cursor.close()
    
    def run_catchup_update(self):
        """初回キャッチアップ更新実行"""
        logging.info("=== 全ナレッジファイル差分更新開始（MySQL生データコピー方式） ===")
        
        if not self.connect_db():
            return False
        
        try:
            results = {}
            
            # 1. D-Logic標準ナレッジ更新
            logging.info("
--- dlogic_raw_knowledge.json 更新開始 ---")
            new_horses = self.get_new_horses_since_date('2025-08-09')
            results['dlogic_raw_knowledge.json'] = self.update_dlogic_raw_knowledge(new_horses)
            
            # 2. 拡張ナレッジ更新  
            logging.info("
--- dlogic_extended_knowledge.json 更新開始 ---")
            new_horses = self.get_new_horses_since_date('2025-08-19')
            results['dlogic_extended_knowledge.json'] = self.update_dlogic_extended_knowledge(new_horses)
            
            # 3. 騎手ナレッジ更新
            logging.info("
--- jockey_knowledge.json 更新開始 ---")
            new_jockeys = self.get_new_jockeys_since_date('2025-08-17')
            results['jockey_knowledge.json'] = self.update_jockey_knowledge(new_jockeys)
            
            # 4. ViewLogicナレッジ更新
            logging.info("
--- viewlogic_knowledge.json 更新開始 ---")
            new_races = self.get_new_races_since_date('2025-08-03')
            results['viewlogic_knowledge.json'] = self.update_viewlogic_knowledge(new_races)
            
            # 結果サマリー
            logging.info("
=== 更新結果サマリー ===")
            for filename, count in results.items():
                logging.info(f"{filename}: {count}件追加")
            
            return True
            
        finally:
            if self.connection:
                self.connection.close()

if __name__ == "__main__":
    updater = IncrementalKnowledgeUpdater()
    success = updater.run_catchup_update()
    
    if success:
        logging.info("全ナレッジファイル差分更新完了")
    else:
        logging.error("差分更新中にエラーが発生しました")