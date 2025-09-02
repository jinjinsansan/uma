#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
D-Logic標準ナレッジファイル差分更新スクリプト
2025-08-09以降の新馬データをMySQLから取得して追加
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
        logging.FileHandler('dlogic_raw_incremental.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class DLogicRawKnowledgeIncremental:
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
    
    def get_new_horses_since_date(self):
        """2025-08-09以降に出走した新馬リストを取得"""
        cursor = self.connection.cursor()
        
        try:
            # 既存馬名リストがある場合とない場合で処理を分ける
            if self.existing_data:
                # 既存馬名リストを除外するクエリ
                existing_horse_names = list(self.existing_data.keys())
                placeholders = ','.join(['%s'] * len(existing_horse_names))
                query = f"""
                SELECT DISTINCT BAMEI, COUNT(*) as race_count
                FROM umagoto_race_joho 
                WHERE KAISAI_NEN >= '2025'
                AND KAISAI_GAPPI >= '0809'
                AND BAMEI IS NOT NULL 
                AND BAMEI != ''
                AND BAMEI NOT IN ({placeholders})
                GROUP BY BAMEI
                HAVING race_count >= 3
                ORDER BY race_count DESC
                """
                cursor.execute(query, existing_horse_names)
            else:
                # 既存馬名リストがない場合（初回実行）
                query = """
                SELECT DISTINCT BAMEI, COUNT(*) as race_count
                FROM umagoto_race_joho 
                WHERE KAISAI_NEN >= '2025'
                AND KAISAI_GAPPI >= '0809'
                AND BAMEI IS NOT NULL 
                AND BAMEI != ''
                GROUP BY BAMEI
                HAVING race_count >= 3
                ORDER BY race_count DESC
                """
                cursor.execute(query)
            
            new_horses = []
            for row in cursor.fetchall():
                horse_name, race_count = row
                new_horses.append({'name': horse_name, 'race_count': race_count})
            
            logging.info(f"新馬リスト取得完了: {len(new_horses)}頭")
            return new_horses
            
        except Exception as e:
            logging.error(f"新馬リスト取得エラー: {e}")
            return []
        finally:
            cursor.close()
    
    def extract_horse_raw_data(self, horse_name):
        """指定馬の生データをMySQLから抽出（既存バッチと同じ構造）"""
        cursor = self.connection.cursor()
        
        # レース履歴取得
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
            
            # 生データ整形（既存バッチと同じ構造）
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
                
                # レース履歴データ
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
            
            # 基本情報（最新レースから）
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
            logging.error(f"馬データ抽出エラー({horse_name}): {e}")
            return None
        finally:
            cursor.close()
    
    def process_new_horses(self, new_horses):
        """新馬データをナレッジファイルに追加"""
        success_count = 0
        error_count = 0
        
        logging.info(f"新馬処理開始: {len(new_horses)}頭")
        
        for idx, horse_info in enumerate(new_horses, 1):
            horse_name = horse_info['name']
            race_count = horse_info['race_count']
            
            try:
                logging.info(f"処理中 ({idx}/{len(new_horses)}): {horse_name} ({race_count}レース)")
                
                # 馬の生データ抽出
                raw_data = self.extract_horse_raw_data(horse_name)
                
                if raw_data and raw_data["race_history"]:
                    # 既存データに追加
                    self.existing_data[horse_name] = raw_data
                    success_count += 1
                    logging.info(f"追加完了: {horse_name}")
                else:
                    logging.warning(f"データ不足のためスキップ: {horse_name}")
                    error_count += 1
                
                # 10頭ごとに中間保存
                if success_count > 0 and success_count % 10 == 0:
                    self.save_knowledge_file()
                    logging.info(f"中間保存完了: {success_count}頭処理済み")
                
                # MySQL負荷軽減のため小休止
                time.sleep(1)
                
            except Exception as e:
                logging.error(f"馬処理エラー({horse_name}): {e}")
                error_count += 1
        
        return success_count, error_count
    
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
            
            # 3. 新馬リスト取得
            new_horses = self.get_new_horses_since_date()
            if not new_horses:
                logging.info("新しい馬は見つかりませんでした")
                return True
            
            # 4. 新馬データ処理
            success_count, error_count = self.process_new_horses(new_horses)
            
            # 5. 最終保存
            self.save_knowledge_file()
            
            # 結果レポート
            elapsed_time = time.time() - start_time
            logging.info("=== 処理完了 ===")
            logging.info(f"新規追加: {success_count}頭")
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
    updater = DLogicRawKnowledgeIncremental()
    success = updater.run()
    
    if success:
        print("D-Logic標準ナレッジファイル差分更新完了")
    else:
        print("差分更新中にエラーが発生しました")