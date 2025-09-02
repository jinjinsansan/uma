#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
拡張ナレッジファイル差分更新スクリプト（I-Logic/IMロジック用）
2025-08-19以降の新馬データをMySQLから取得して追加
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
        logging.FileHandler('extended_knowledge_incremental.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class ExtendedKnowledgeIncremental:
    def __init__(self):
        self.connection = None
        self.existing_data = {}
        self.since_date = '2025-08-19'  # 拡張ナレッジファイル作成日
        
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
        """既存の拡張ナレッジファイルを読み込み"""
        filepath = 'data/dlogic_extended_knowledge.json'
        
        if not os.path.exists(filepath):
            logging.error(f"{filepath} が見つかりません")
            return False
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.existing_data = json.load(f)
            
            logging.info(f"既存拡張ナレッジファイル読み込み完了: {len(self.existing_data)}頭")
            return True
            
        except Exception as e:
            logging.error(f"拡張ナレッジファイル読み込みエラー: {e}")
            return False
    
    def get_new_horses_since_date(self):
        """2025-08-19以降に出走した新馬リストを取得"""
        cursor = self.connection.cursor()
        
        query = """
        SELECT DISTINCT BAMEI, COUNT(*) as race_count
        FROM umagoto_race_joho 
        WHERE KAISAI_NEN >= '2025'
        AND KAISAI_GAPPI >= '0819'
        AND BAMEI IS NOT NULL 
        AND BAMEI != ''
        AND BAMEI NOT IN %s
        GROUP BY BAMEI
        HAVING race_count >= 1
        ORDER BY race_count DESC
        """
        
        try:
            # 既存馬名リストを除外条件に使用
            existing_horses = tuple(self.existing_data.keys()) if self.existing_data else ('',)
            cursor.execute(query, (existing_horses,))
            
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
    
    def extract_extended_horse_data(self, horse_name):
        """指定馬の拡張データをMySQLから抽出（I-Logic用データ構造）"""
        cursor = self.connection.cursor()
        
        # より詳細な拡張情報を取得
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
            u.NYUSEN_JUNI as total_horses,
            r.KYORI as distance,
            r.TRACK_CODE as track,
            r.TENKO_CODE as weather,
            r.GRADE_CODE as grade,
            r.RACE_MEI as race_name,
            r.KEIBAJO_CODE as venue_code,
            k.KETTO1_BAMEI as sire_name,
            k.KETTO2_BAMEI as dam_name
        FROM umagoto_race_joho u
        LEFT JOIN race_shosai r ON u.RACE_CODE = r.RACE_CODE
        LEFT JOIN kyosoba_master2 k ON u.KETTO_TOROKU_BANGO = k.KETTO_TOROKU_BANGO
        WHERE u.BAMEI = %s
        AND u.KAISAI_NEN IS NOT NULL
        ORDER BY u.KAISAI_NEN DESC, u.KAISAI_GAPPI DESC
        """
        
        try:
            cursor.execute(query, (horse_name,))
            races = cursor.fetchall()
            
            # 拡張データ整形（I-Logic用）
            race_history = []
            extended_stats = {
                "total_races": 0,
                "wins": 0,
                "win_rate": 0.0,
                "place_rate": 0.0,
                "distance_performance": {},
                "jockey_performance": {},
                "trainer_performance": {},
                "venue_performance": {},
                "track_condition_stats": {},
                "grade_performance": {},
                "recent_form": []  # 最新5走の傾向
            }
            
            for race in races:
                race_dict = {
                    "race_code": race[0],
                    "year": race[1],
                    "date": race[2],
                    "finish": race[3],
                    "odds": race[4],
                    "popularity": race[5],
                    "weight": race[6],
                    "horse_weight": race[7],
                    "weight_change": race[8],
                    "jockey": race[9],
                    "trainer": race[10],
                    "corner1": race[11],
                    "corner2": race[12],
                    "corner3": race[13],
                    "corner4": race[14],
                    "time": race[15],
                    "age": race[16],
                    "sex": race[17],
                    "total_horses": race[18],
                    "distance": race[19],
                    "track": race[20],
                    "weather": race[21],
                    "grade": race[22],
                    "race_name": race[23],
                    "venue_code": race[24],
                    "sire_name": race[25],
                    "dam_name": race[26]
                }
                
                # レース履歴データ（拡張版）
                race_data = {
                    "race_code": race_dict.get("race_code"),
                    "date": f"{race_dict.get('year', '')}{race_dict.get('date', '')}" if race_dict.get('year') and race_dict.get('date') else None,
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
                    "track": race_dict.get("track"),
                    "weather": race_dict.get("weather"),
                    "grade": race_dict.get("grade"),
                    "race_name": race_dict.get("race_name"),
                    "venue_code": race_dict.get("venue_code"),
                    "sire_name": race_dict.get("sire_name"),
                    "dam_name": race_dict.get("dam_name"),
                    "total_horses": int(race_dict["total_horses"]) if race_dict.get("total_horses") and str(race_dict["total_horses"]).isdigit() else None
                }
                
                # コーナー順位（拡張版）
                for i in range(1, 5):
                    corner_key = f"corner{i}"
                    corner = race_dict.get(corner_key)
                    if corner and str(corner).isdigit():
                        race_data["corner_positions"].append(int(corner))
                
                if race_data["finish"]:
                    race_history.append(race_data)
                    
                    # 拡張集計データ更新
                    extended_stats["total_races"] += 1
                    if race_data["finish"] == 1:
                        extended_stats["wins"] += 1
                    
                    # 距離別成績
                    if race_data["distance"]:
                        dist_key = str(race_data["distance"])
                        if dist_key not in extended_stats["distance_performance"]:
                            extended_stats["distance_performance"][dist_key] = []
                        extended_stats["distance_performance"][dist_key].append(race_data["finish"])
                    
                    # 騎手別成績
                    if race_data["jockey"]:
                        if race_data["jockey"] not in extended_stats["jockey_performance"]:
                            extended_stats["jockey_performance"][race_data["jockey"]] = []
                        extended_stats["jockey_performance"][race_data["jockey"]].append(race_data["finish"])
                    
                    # 調教師別成績
                    if race_data["trainer"]:
                        if race_data["trainer"] not in extended_stats["trainer_performance"]:
                            extended_stats["trainer_performance"][race_data["trainer"]] = []
                        extended_stats["trainer_performance"][race_data["trainer"]].append(race_data["finish"])
                    
                    # 会場別成績
                    if race_data["venue_code"]:
                        if race_data["venue_code"] not in extended_stats["venue_performance"]:
                            extended_stats["venue_performance"][race_data["venue_code"]] = []
                        extended_stats["venue_performance"][race_data["venue_code"]].append(race_data["finish"])
                    
                    # 馬場状態別成績
                    if race_data["track"]:
                        track_key = race_data["track"]
                        if track_key not in extended_stats["track_condition_stats"]:
                            extended_stats["track_condition_stats"][track_key] = []
                        extended_stats["track_condition_stats"][track_key].append(race_data["finish"])
                    
                    # グレード別成績
                    if race_data["grade"]:
                        grade_key = race_data["grade"]
                        if grade_key not in extended_stats["grade_performance"]:
                            extended_stats["grade_performance"][grade_key] = []
                        extended_stats["grade_performance"][grade_key].append(race_data["finish"])
            
            # 勝率・複勝率計算
            if extended_stats["total_races"] > 0:
                extended_stats["win_rate"] = extended_stats["wins"] / extended_stats["total_races"] * 100
                places = sum(1 for race in race_history if race["finish"] and race["finish"] <= 3)
                extended_stats["place_rate"] = places / extended_stats["total_races"] * 100
            
            # 最近5走の傾向
            extended_stats["recent_form"] = [race["finish"] for race in race_history[:5] if race["finish"]]
            
            # 基本情報（最新レースから）
            basic_info = {}
            if race_history:
                latest = race_history[0]
                basic_info = {
                    "sex": latest.get("sex"),
                    "age": latest.get("age"),
                    "last_race_date": latest.get("date"),
                    "sire_name": latest.get("sire_name"),
                    "dam_name": latest.get("dam_name")
                }
            
            return {
                "basic_info": basic_info,
                "race_history": race_history[:100],  # 最新100レースまで（拡張版）
                "extended_stats": extended_stats
            }
            
        except Exception as e:
            logging.error(f"拡張馬データ抽出エラー({horse_name}): {e}")
            return None
        finally:
            cursor.close()
    
    def process_new_horses(self, new_horses):
        """新馬データを拡張ナレッジファイルに追加"""
        success_count = 0
        error_count = 0
        
        logging.info(f"新馬処理開始: {len(new_horses)}頭")
        
        for idx, horse_info in enumerate(new_horses, 1):
            horse_name = horse_info['name']
            race_count = horse_info['race_count']
            
            try:
                logging.info(f"処理中 ({idx}/{len(new_horses)}): {horse_name} ({race_count}レース)")
                
                # 馬の拡張データ抽出
                extended_data = self.extract_extended_horse_data(horse_name)
                
                if extended_data and extended_data["race_history"]:
                    # 既存データに追加
                    self.existing_data[horse_name] = extended_data
                    success_count += 1
                    logging.info(f"追加完了: {horse_name}")
                else:
                    logging.warning(f"データ不足のためスキップ: {horse_name}")
                    error_count += 1
                
                # 5頭ごとに中間保存
                if success_count > 0 and success_count % 5 == 0:
                    self.save_knowledge_file()
                    logging.info(f"中間保存完了: {success_count}頭処理済み")
                
                # MySQL負荷軽減のため休止
                time.sleep(2)
                
            except Exception as e:
                logging.error(f"馬処理エラー({horse_name}): {e}")
                error_count += 1
        
        return success_count, error_count
    
    def save_knowledge_file(self):
        """拡張ナレッジファイルを保存"""
        filepath = 'data/dlogic_extended_knowledge.json'
        backup_filepath = f'data/dlogic_extended_knowledge_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
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
            
            logging.info(f"拡張ナレッジファイル保存完了: {len(self.existing_data)}頭")
            
        except Exception as e:
            logging.error(f"ファイル保存エラー: {e}")
    
    def run(self):
        """メイン処理実行"""
        logging.info("=== 拡張ナレッジファイル差分更新開始 ===")
        start_time = time.time()
        
        try:
            # 1. MySQL接続
            if not self.connect_db():
                return False
            
            # 2. 既存拡張ナレッジファイル読み込み
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
    updater = ExtendedKnowledgeIncremental()
    success = updater.run()
    
    if success:
        print("拡張ナレッジファイル差分更新完了")
    else:
        print("差分更新中にエラーが発生しました")