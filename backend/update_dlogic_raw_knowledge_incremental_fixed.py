#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
D-Logic標準ナレッジファイル差分更新スクリプト（修正版）
2025-08-09以降の全レースデータを差分更新
- 既存の馬: 新しいレースを race_history に追加
- 新しい馬: 馬ごと新規追加
- 全ての馬: aggregated_stats を再計算
"""

import json
import os
import mysql.connector
from datetime import datetime
import logging
import time

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('dlogic_incremental_update.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class DLogicIncrementalUpdater:
    def __init__(self):
        self.connection = None
        self.existing_data = {}
        self.since_date = '2025-08-09'  # D-Logicナレッジファイル作成日
        
    def connect_db(self):
        """MySQL接続"""
        try:
            self.connection = mysql.connector.connect(
                host='172.25.160.1',
                user='root',
                password='04050405Aoi-',
                database='mykeibadb',
                charset='utf8mb4',
                collation='utf8mb4_general_ci',
                autocommit=True,
                connection_timeout=30,
                pool_reset_session=False
            )
            logging.info("MySQL接続成功")
            return True
        except Exception as e:
            logging.error(f"MySQL接続エラー: {e}")
            return False
    
    def load_existing_knowledge(self):
        """既存のD-Logic標準ナレッジファイルを読み込み"""
        filepath = 'data/dlogic_raw_knowledge.json'
        
        if not os.path.exists(filepath):
            logging.error(f"{filepath} が見つかりません")
            return False
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.existing_data = json.load(f)
            
            logging.info(f"既存ナレッジファイル読み込み完了: {len(self.existing_data)}頭")
            return True
            
        except Exception as e:
            logging.error(f"ナレッジファイル読み込みエラー: {e}")
            return False
    
    def get_all_horses_with_new_races(self):
        """2025-08-09以降に出走した全ての馬を取得"""
        cursor = self.connection.cursor()
        
        query = """
        SELECT DISTINCT BAMEI, COUNT(*) as race_count
        FROM umagoto_race_joho 
        WHERE KAISAI_NEN >= '2025'
        AND KAISAI_GAPPI >= '0809'
        AND BAMEI IS NOT NULL 
        AND BAMEI != ''
        GROUP BY BAMEI
        HAVING race_count >= 1
        ORDER BY race_count DESC
        """
        
        try:
            cursor.execute(query)
            
            horses = []
            for row in cursor.fetchall():
                horse_name, race_count = row
                is_existing = horse_name in self.existing_data
                horses.append({
                    'name': horse_name, 
                    'race_count': race_count,
                    'is_existing': is_existing
                })
            
            new_horses = [h for h in horses if not h['is_existing']]
            existing_horses = [h for h in horses if h['is_existing']]
            
            logging.info(f"対象馬取得完了: 新規{len(new_horses)}頭、既存{len(existing_horses)}頭")
            return new_horses, existing_horses
            
        except Exception as e:
            logging.error(f"対象馬取得エラー: {e}")
            return [], []
        finally:
            cursor.close()
    
    def get_horse_races_since_date(self, horse_name, since_date):
        """指定馬の指定日以降のレースデータを取得"""
        cursor = self.connection.cursor()
        
        query = """
        SELECT 
            u.RACE_CODE,
            u.KAISAI_NEN,
            u.KAISAI_GAPPI,
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
        AND u.KAISAI_NEN >= '2025'
        AND u.KAISAI_GAPPI >= %s
        AND u.KAISAI_NEN IS NOT NULL
        ORDER BY u.KAISAI_NEN DESC, u.KAISAI_GAPPI DESC
        """
        
        try:
            cursor.execute(query, (horse_name, since_date.replace('-', '')[4:]))
            races = cursor.fetchall()
            
            new_races = []
            for race in races:
                race_dict = {
                    "RACE_CODE": race[0],
                    "KAISAI_NEN": race[1],
                    "KAISAI_GAPPI": race[2],
                    "finish": race[3],
                    "odds": race[4],
                    "popularity": race[5],
                    "weight": race[6],
                    "horse_weight": race[7],
                    "weight_change": race[8],
                    "jockey": race[9],
                    "trainer": race[10],
                    "CORNER1_JUNI": race[11],
                    "CORNER2_JUNI": race[12],
                    "CORNER3_JUNI": race[13],
                    "CORNER4_JUNI": race[14],
                    "time": race[15],
                    "age": race[16],
                    "sex": race[17],
                    "distance": race[18],
                    "track": race[19]
                }
                
                # レースデータ整形
                race_data = {
                    "race_code": race_dict.get("RACE_CODE"),
                    "date": f"{race_dict.get('KAISAI_NEN', '')}{race_dict.get('KAISAI_GAPPI', '')}" if race_dict.get('KAISAI_NEN') and race_dict.get('KAISAI_GAPPI') else None,
                    "finish": int(race_dict["finish"]) if race_dict.get("finish") and str(race_dict["finish"]).isdigit() else None,
                    "odds": float(race_dict["odds"]) / 10 if race_dict.get("odds") and str(race_dict["odds"]).isdigit() else None,
                    "popularity": int(race_dict["popularity"]) if race_dict.get("popularity") and str(race_dict["popularity"]).isdigit() else None,
                    "weight": int(race_dict["weight"]) if race_dict.get("weight") and str(race_dict["weight"]).isdigit() else None,
                    "horse_weight": int(race_dict["horse_weight"]) if race_dict.get("horse_weight") and str(race_dict["horse_weight"]).isdigit() else None,
                    "weight_change": race_dict.get("weight_change"),
                    "jockey": race_dict.get("jockey"),
                    "trainer": race_dict.get("trainer"),
                    "corner_positions": [],
                    "time": float(race_dict["time"]) / 10 if race_dict.get("time") and str(race_dict["time"]).isdigit() else None,
                    "age": int(race_dict["age"]) if race_dict.get("age") and str(race_dict["age"]).isdigit() else None,
                    "sex": race_dict.get("sex"),
                    "distance": int(race_dict["distance"]) if race_dict.get("distance") and str(race_dict["distance"]).isdigit() else None,
                    "track": race_dict.get("track")
                }
                
                # コーナー順位
                for i in range(1, 5):
                    corner = race_dict.get(f"CORNER{i}_JUNI")
                    if corner and str(corner).isdigit():
                        race_data["corner_positions"].append(int(corner))
                
                if race_data["finish"]:
                    new_races.append(race_data)
            
            return new_races
            
        except Exception as e:
            logging.error(f"馬のレースデータ取得エラー({horse_name}): {e}")
            return []
        finally:
            cursor.close()
    
    def get_horse_all_races(self, horse_name):
        """指定馬の全レースデータを取得（新規馬用）"""
        cursor = self.connection.cursor()
        
        query = """
        SELECT 
            u.RACE_CODE,
            u.KAISAI_NEN,
            u.KAISAI_GAPPI,
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
        AND u.KAISAI_NEN IS NOT NULL
        ORDER BY u.KAISAI_NEN DESC, u.KAISAI_GAPPI DESC
        """
        
        try:
            cursor.execute(query, (horse_name,))
            races = cursor.fetchall()
            
            # 既存のextract_horse_raw_dataと同じロジック
            race_history = []
            aggregated_stats = {
                "total_races": 0,
                "wins": 0,
                "distance_performance": {},
                "jockey_performance": {},
                "trainer_performance": {}
            }
            
            for race in races:
                race_dict = {
                    "RACE_CODE": race[0],
                    "KAISAI_NEN": race[1],
                    "KAISAI_GAPPI": race[2],
                    "finish": race[3],
                    "odds": race[4],
                    "popularity": race[5],
                    "weight": race[6],
                    "horse_weight": race[7],
                    "weight_change": race[8],
                    "jockey": race[9],
                    "trainer": race[10],
                    "CORNER1_JUNI": race[11],
                    "CORNER2_JUNI": race[12],
                    "CORNER3_JUNI": race[13],
                    "CORNER4_JUNI": race[14],
                    "time": race[15],
                    "age": race[16],
                    "sex": race[17],
                    "distance": race[18],
                    "track": race[19]
                }
                
                race_data = {
                    "race_code": race_dict.get("RACE_CODE"),
                    "date": f"{race_dict.get('KAISAI_NEN', '')}{race_dict.get('KAISAI_GAPPI', '')}" if race_dict.get('KAISAI_NEN') and race_dict.get('KAISAI_GAPPI') else None,
                    "finish": int(race_dict["finish"]) if race_dict.get("finish") and str(race_dict["finish"]).isdigit() else None,
                    "odds": float(race_dict["odds"]) / 10 if race_dict.get("odds") and str(race_dict["odds"]).isdigit() else None,
                    "popularity": int(race_dict["popularity"]) if race_dict.get("popularity") and str(race_dict["popularity"]).isdigit() else None,
                    "weight": int(race_dict["weight"]) if race_dict.get("weight") and str(race_dict["weight"]).isdigit() else None,
                    "horse_weight": int(race_dict["horse_weight"]) if race_dict.get("horse_weight") and str(race_dict["horse_weight"]).isdigit() else None,
                    "weight_change": race_dict.get("weight_change"),
                    "jockey": race_dict.get("jockey"),
                    "trainer": race_dict.get("trainer"),
                    "corner_positions": [],
                    "time": float(race_dict["time"]) / 10 if race_dict.get("time") and str(race_dict["time"]).isdigit() else None,
                    "age": int(race_dict["age"]) if race_dict.get("age") and str(race_dict["age"]).isdigit() else None,
                    "sex": race_dict.get("sex"),
                    "distance": int(race_dict["distance"]) if race_dict.get("distance") and str(race_dict["distance"]).isdigit() else None,
                    "track": race_dict.get("track")
                }
                
                # コーナー順位
                for i in range(1, 5):
                    corner = race_dict.get(f"CORNER{i}_JUNI")
                    if corner and str(corner).isdigit():
                        race_data["corner_positions"].append(int(corner))
                
                if race_data["finish"]:
                    race_history.append(race_data)
                    
                    # 集計データ更新
                    aggregated_stats["total_races"] += 1
                    if race_data["finish"] == 1:
                        aggregated_stats["wins"] += 1
                    
                    # 距離別成績
                    if race_data["distance"]:
                        dist_key = str(race_data["distance"])
                        if dist_key not in aggregated_stats["distance_performance"]:
                            aggregated_stats["distance_performance"][dist_key] = []
                        aggregated_stats["distance_performance"][dist_key].append(race_data["finish"])
                    
                    # 騎手別成績
                    if race_data["jockey"]:
                        if race_data["jockey"] not in aggregated_stats["jockey_performance"]:
                            aggregated_stats["jockey_performance"][race_data["jockey"]] = []
                        aggregated_stats["jockey_performance"][race_data["jockey"]].append(race_data["finish"])
                    
                    # 調教師別成績
                    if race_data["trainer"]:
                        if race_data["trainer"] not in aggregated_stats["trainer_performance"]:
                            aggregated_stats["trainer_performance"][race_data["trainer"]] = []
                        aggregated_stats["trainer_performance"][race_data["trainer"]].append(race_data["finish"])
            
            # 基本情報
            basic_info = {}
            if race_history:
                latest = race_history[0]
                basic_info = {
                    "sex": latest.get("sex"),
                    "age": latest.get("age"),
                    "last_race_date": latest.get("date")
                }
            
            return {
                "basic_info": basic_info,
                "race_history": race_history[:50],  # 最新50レースまで
                "aggregated_stats": aggregated_stats
            }
            
        except Exception as e:
            logging.error(f"馬の全レースデータ取得エラー({horse_name}): {e}")
            return None
        finally:
            cursor.close()
    
    def recalculate_aggregated_stats(self, race_history):
        """レース履歴から集計データを再計算"""
        aggregated_stats = {
            "total_races": 0,
            "wins": 0,
            "distance_performance": {},
            "jockey_performance": {},
            "trainer_performance": {}
        }
        
        for race_data in race_history:
            if race_data.get("finish"):
                aggregated_stats["total_races"] += 1
                if race_data["finish"] == 1:
                    aggregated_stats["wins"] += 1
                
                # 距離別成績
                if race_data.get("distance"):
                    dist_key = str(race_data["distance"])
                    if dist_key not in aggregated_stats["distance_performance"]:
                        aggregated_stats["distance_performance"][dist_key] = []
                    aggregated_stats["distance_performance"][dist_key].append(race_data["finish"])
                
                # 騎手別成績
                if race_data.get("jockey"):
                    if race_data["jockey"] not in aggregated_stats["jockey_performance"]:
                        aggregated_stats["jockey_performance"][race_data["jockey"]] = []
                    aggregated_stats["jockey_performance"][race_data["jockey"]].append(race_data["finish"])
                
                # 調教師別成績
                if race_data.get("trainer"):
                    if race_data["trainer"] not in aggregated_stats["trainer_performance"]:
                        aggregated_stats["trainer_performance"][race_data["trainer"]] = []
                    aggregated_stats["trainer_performance"][race_data["trainer"]].append(race_data["finish"])
        
        return aggregated_stats
    
    def process_horses(self, new_horses, existing_horses):
        """馬データの処理"""
        success_count = 0
        error_count = 0
        updated_count = 0
        
        total_horses = len(new_horses) + len(existing_horses)
        logging.info(f"馬データ処理開始: 新規{len(new_horses)}頭、既存更新{len(existing_horses)}頭")
        
        # 1. 新規馬の追加
        for idx, horse_info in enumerate(new_horses, 1):
            horse_name = horse_info['name']
            
            try:
                logging.info(f"新規馬処理 ({idx}/{len(new_horses)}): {horse_name}")
                
                raw_data = self.get_horse_all_races(horse_name)
                
                if raw_data and raw_data["race_history"]:
                    self.existing_data[horse_name] = raw_data
                    success_count += 1
                    logging.info(f"新規追加完了: {horse_name}")
                else:
                    logging.warning(f"データ不足のためスキップ: {horse_name}")
                    error_count += 1
                
                # 10頭ごとに中間保存
                if success_count > 0 and success_count % 10 == 0:
                    self.save_knowledge_file()
                    logging.info(f"中間保存完了: {success_count}頭処理済み")
                
                time.sleep(1)
                
            except Exception as e:
                logging.error(f"新規馬処理エラー({horse_name}): {e}")
                error_count += 1
        
        # 2. 既存馬の更新
        for idx, horse_info in enumerate(existing_horses, 1):
            horse_name = horse_info['name']
            
            try:
                logging.info(f"既存馬更新 ({idx}/{len(existing_horses)}): {horse_name}")
                
                # 2025-08-09以降の新しいレース取得
                new_races = self.get_horse_races_since_date(horse_name, self.since_date)
                
                if new_races:
                    # 既存のrace_historyに新しいレースを追加（重複除去）
                    existing_race_codes = {race.get('race_code') for race in self.existing_data[horse_name]['race_history']}
                    new_unique_races = [race for race in new_races if race.get('race_code') not in existing_race_codes]
                    
                    if new_unique_races:
                        # レース履歴を更新（新しいレースを先頭に追加）
                        self.existing_data[horse_name]['race_history'] = new_unique_races + self.existing_data[horse_name]['race_history']
                        
                        # 最新50レースまでに制限
                        self.existing_data[horse_name]['race_history'] = self.existing_data[horse_name]['race_history'][:50]
                        
                        # aggregated_statsを再計算
                        self.existing_data[horse_name]['aggregated_stats'] = self.recalculate_aggregated_stats(
                            self.existing_data[horse_name]['race_history']
                        )
                        
                        # basic_infoを更新
                        if self.existing_data[horse_name]['race_history']:
                            latest = self.existing_data[horse_name]['race_history'][0]
                            self.existing_data[horse_name]['basic_info'] = {
                                "sex": latest.get("sex"),
                                "age": latest.get("age"),
                                "last_race_date": latest.get("date")
                            }
                        
                        updated_count += 1
                        logging.info(f"既存馬更新完了: {horse_name} ({len(new_unique_races)}レース追加)")
                    else:
                        logging.info(f"新しいレースなし: {horse_name}")
                else:
                    logging.info(f"新しいレースなし: {horse_name}")
                
                # 10頭ごとに中間保存
                if updated_count > 0 and updated_count % 10 == 0:
                    self.save_knowledge_file()
                    logging.info(f"中間保存完了: {updated_count}頭更新済み")
                
                time.sleep(1)
                
            except Exception as e:
                logging.error(f"既存馬更新エラー({horse_name}): {e}")
                error_count += 1
        
        return success_count, updated_count, error_count
    
    def save_knowledge_file(self):
        """ナレッジファイルを保存"""
        filepath = 'data/dlogic_raw_knowledge.json'
        backup_filepath = f'data/dlogic_raw_knowledge_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        try:
            # バックアップ作成
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    backup_data = json.load(f)
                with open(backup_filepath, 'w', encoding='utf-8') as f:
                    json.dump(backup_data, f, ensure_ascii=False, indent=2)
                logging.info(f"バックアップ作成: {backup_filepath}")
            
            # 新しいファイル保存
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.existing_data, f, ensure_ascii=False, indent=2)
            
            logging.info(f"ナレッジファイル保存完了: {len(self.existing_data)}頭")
            
        except Exception as e:
            logging.error(f"ファイル保存エラー: {e}")
    
    def run(self):
        """メイン処理実行"""
        logging.info("=== D-Logic標準ナレッジファイル差分更新開始 ===")
        start_time = time.time()
        
        try:
            # 1. MySQL接続
            if not self.connect_db():
                return False
            
            # 2. 既存ナレッジファイル読み込み
            if not self.load_existing_knowledge():
                return False
            
            # 3. 対象馬リスト取得
            new_horses, existing_horses = self.get_all_horses_with_new_races()
            if not new_horses and not existing_horses:
                logging.info("更新対象の馬は見つかりませんでした")
                return True
            
            # 4. 馬データ処理
            success_count, updated_count, error_count = self.process_horses(new_horses, existing_horses)
            
            # 5. 最終保存
            self.save_knowledge_file()
            
            # 結果レポート
            elapsed_time = time.time() - start_time
            logging.info("=== 処理完了 ===")
            logging.info(f"新規追加: {success_count}頭")
            logging.info(f"既存更新: {updated_count}頭")
            logging.info(f"エラー: {error_count}頭")
            logging.info(f"総馬数: {len(self.existing_data)}頭")
            logging.info(f"処理時間: {elapsed_time/60:.1f}分")
            
            return True
            
        except Exception as e:
            logging.error(f"メイン処理エラー: {e}")
            return False
        finally:
            if self.connection:
                self.connection.close()
                logging.info("MySQL接続終了")

if __name__ == "__main__":
    updater = DLogicIncrementalUpdater()
    success = updater.run()
    
    if success:
        print("D-Logic標準ナレッジファイル差分更新完了")
    else:
        print("差分更新中にエラーが発生しました")