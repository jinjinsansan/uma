#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ViewLogicナレッジファイル差分更新スクリプト
2025-08-09以降の全レースデータを差分更新
- 既存の馬: 新しいレースを races リストに追加し、Phaseを更新
- 新しい馬: 馬ごと新規追加
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
        logging.FileHandler('viewlogic_knowledge_incremental.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class ViewLogicKnowledgeIncrementalUpdater:
    def __init__(self):
        self.connection = None
        self.existing_data = {}
        self.since_date = '2025-08-09'  # ViewLogicナレッジファイル作成日
        
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
        """既存のViewLogicナレッジファイルを読み込み"""
        filepath = 'data/viewlogic_knowledge.json'
        
        if not os.path.exists(filepath):
            logging.error(f"{filepath} が見つかりません")
            return False
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
            
            # ViewLogicナレッジファイル構造: {"metadata": {...}, "horses": [...]}
            if "horses" in raw_data:
                # 馬名をキーとした辞書に変換
                self.existing_data = {}
                for horse in raw_data["horses"]:
                    if "horse_name" in horse:
                        self.existing_data[horse["horse_name"]] = horse
                
                logging.info(f"既存ViewLogicナレッジファイル読み込み完了: {len(self.existing_data)}頭")
                self.metadata = raw_data.get("metadata", {})
                return True
            else:
                logging.error("ViewLogicナレッジファイルの構造が不正です")
                return False
            
        except Exception as e:
            logging.error(f"ViewLogicナレッジファイル読み込みエラー: {e}")
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
        """指定馬の指定日以降のレースデータを取得（ViewLogic形式）"""
        cursor = self.connection.cursor()
        
        query = """
        SELECT 
            u.BAMEI,
            u.KAISAI_NEN,
            u.KAISAI_GAPPI,
            u.KAKUTEI_CHAKUJUN,
            u.KISHUMEI_RYAKUSHO,
            u.CORNER1_JUNI,
            u.CORNER2_JUNI,
            u.CORNER3_JUNI,
            u.CORNER4_JUNI,
            u.SOHA_TIME,
            r.KYORI,
            r.KEIBAJO_CODE,
            r.RACE_MEI
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
                race_data = {
                    "BAMEI": race[0],
                    "KAISAI_NEN": race[1],
                    "KAISAI_GAPPI": race[2], 
                    "KAKUTEI_CHAKUJUN": race[3],
                    "KISHUMEI_RYAKUSHO": race[4],
                    "CORNER1_JUNI": race[5],
                    "CORNER2_JUNI": race[6], 
                    "CORNER3_JUNI": race[7],
                    "CORNER4_JUNI": race[8],
                    "SOHA_TIME": race[9],
                    "KYORI": race[10],
                    "KEIBAJO_CODE": race[11],
                    "RACE_MEI": race[12]
                }
                
                # ViewLogicで使用する形式で格納
                if race_data["KAKUTEI_CHAKUJUN"]:
                    new_races.append(race_data)
            
            return new_races
            
        except Exception as e:
            logging.error(f"馬のレースデータ取得エラー({horse_name}): {e}")
            return []
        finally:
            cursor.close()
    
    def get_horse_all_races(self, horse_name):
        """指定馬の全レースデータを取得（新規馬用・ViewLogic形式）"""
        cursor = self.connection.cursor()
        
        query = """
        SELECT 
            u.BAMEI,
            u.KAISAI_NEN,
            u.KAISAI_GAPPI,
            u.KAKUTEI_CHAKUJUN,
            u.KISHUMEI_RYAKUSHO,
            u.CORNER1_JUNI,
            u.CORNER2_JUNI,
            u.CORNER3_JUNI,
            u.CORNER4_JUNI,
            u.SOHA_TIME,
            r.KYORI,
            r.KEIBAJO_CODE,
            r.RACE_MEI
        FROM umagoto_race_joho u
        LEFT JOIN race_shosai r ON u.RACE_CODE = r.RACE_CODE
        WHERE u.BAMEI = %s
        AND u.KAISAI_NEN IS NOT NULL
        ORDER BY u.KAISAI_NEN DESC, u.KAISAI_GAPPI DESC
        """
        
        try:
            cursor.execute(query, (horse_name,))
            races = cursor.fetchall()
            
            race_history = []
            for race in races:
                race_data = {
                    "BAMEI": race[0],
                    "KAISAI_NEN": race[1],
                    "KAISAI_GAPPI": race[2],
                    "KAKUTEI_CHAKUJUN": race[3],
                    "KISHUMEI_RYAKUSHO": race[4],
                    "CORNER1_JUNI": race[5],
                    "CORNER2_JUNI": race[6],
                    "CORNER3_JUNI": race[7],
                    "CORNER4_JUNI": race[8],
                    "SOHA_TIME": race[9],
                    "KYORI": race[10],
                    "KEIBAJO_CODE": race[11],
                    "RACE_MEI": race[12]
                }
                
                if race_data["KAKUTEI_CHAKUJUN"]:
                    race_history.append(race_data)
            
            # ViewLogic形式のPhase判定（レース数に基づく）
            total_races = len(race_history)
            if total_races >= 20:
                phase = 5
            elif total_races >= 15:
                phase = 4
            elif total_races >= 10:
                phase = 3
            elif total_races >= 5:
                phase = 2
            else:
                phase = 1
            
            return {
                "horse_name": horse_name,
                "phase": phase,
                "total_races": total_races,
                "races": race_history[:50]  # 最新50レースまで
            }
            
        except Exception as e:
            logging.error(f"馬の全レースデータ取得エラー({horse_name}): {e}")
            return None
        finally:
            cursor.close()
    
    def update_horse_phase(self, horse_data):
        """馬のPhaseを総レース数に基づいて更新"""
        total_races = len(horse_data.get("races", []))
        
        if total_races >= 20:
            horse_data["phase"] = 5
        elif total_races >= 15:
            horse_data["phase"] = 4
        elif total_races >= 10:
            horse_data["phase"] = 3
        elif total_races >= 5:
            horse_data["phase"] = 2
        else:
            horse_data["phase"] = 1
        
        horse_data["total_races"] = total_races
        return horse_data
    
    def process_horses(self, new_horses, existing_horses):
        """馬データの処理"""
        success_count = 0
        error_count = 0
        updated_count = 0
        
        logging.info(f"ViewLogic馬データ処理開始: 新規{len(new_horses)}頭、既存更新{len(existing_horses)}頭")
        
        # 1. 新規馬の追加
        for idx, horse_info in enumerate(new_horses, 1):
            horse_name = horse_info['name']
            
            try:
                logging.info(f"新規馬処理 ({idx}/{len(new_horses)}): {horse_name}")
                
                horse_data = self.get_horse_all_races(horse_name)
                
                if horse_data and horse_data["races"]:
                    self.existing_data[horse_name] = horse_data
                    success_count += 1
                    logging.info(f"新規追加完了: {horse_name} (Phase {horse_data['phase']}, {horse_data['total_races']}レース)")
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
                    # 既存のレース一覧から重複除去用のセット作成
                    existing_race_keys = set()
                    for race in self.existing_data[horse_name].get("races", []):
                        race_key = f"{race.get('KAISAI_NEN', '')}_{race.get('KAISAI_GAPPI', '')}_{race.get('BAMEI', '')}"
                        existing_race_keys.add(race_key)
                    
                    # 新しいレースから重複を除去
                    new_unique_races = []
                    for race in new_races:
                        race_key = f"{race.get('KAISAI_NEN', '')}_{race.get('KAISAI_GAPPI', '')}_{race.get('BAMEI', '')}"
                        if race_key not in existing_race_keys:
                            new_unique_races.append(race)
                    
                    if new_unique_races:
                        # 新しいレースを既存レース一覧の先頭に追加
                        self.existing_data[horse_name]["races"] = new_unique_races + self.existing_data[horse_name].get("races", [])
                        
                        # 最新50レースまでに制限
                        self.existing_data[horse_name]["races"] = self.existing_data[horse_name]["races"][:50]
                        
                        # Phase更新
                        self.existing_data[horse_name] = self.update_horse_phase(self.existing_data[horse_name])
                        
                        updated_count += 1
                        logging.info(f"既存馬更新完了: {horse_name} ({len(new_unique_races)}レース追加, Phase {self.existing_data[horse_name]['phase']})")
                    else:
                        logging.info(f"新しいレースなし（重複）: {horse_name}")
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
        """ViewLogicナレッジファイルを保存（元の形式）"""
        filepath = 'data/viewlogic_knowledge.json'
        backup_filepath = f'data/viewlogic_knowledge_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        try:
            # バックアップ作成
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    backup_data = json.load(f)
                with open(backup_filepath, 'w', encoding='utf-8') as f:
                    json.dump(backup_data, f, ensure_ascii=False, indent=2)
                logging.info(f"バックアップ作成: {backup_filepath}")
            
            # ViewLogic形式でファイル保存
            output_data = {
                "metadata": getattr(self, 'metadata', {
                    "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "total_horses": len(self.existing_data)
                }),
                "horses": list(self.existing_data.values())
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            
            logging.info(f"ViewLogicナレッジファイル保存完了: {len(self.existing_data)}頭")
            
        except Exception as e:
            logging.error(f"ファイル保存エラー: {e}")
    
    def run(self):
        """メイン処理実行"""
        logging.info("=== ViewLogicナレッジファイル差分更新開始 ===")
        start_time = time.time()
        
        try:
            # 1. MySQL接続
            if not self.connect_db():
                return False
            
            # 2. 既存ViewLogicナレッジファイル読み込み
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
    updater = ViewLogicKnowledgeIncrementalUpdater()
    success = updater.run()
    
    if success:
        print("ViewLogicナレッジファイル差分更新完了")
    else:
        print("差分更新中にエラーが発生しました")