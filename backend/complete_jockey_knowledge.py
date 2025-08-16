#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
騎手ナレッジファイル完全版作成スクリプト
1,071名全員のデータを確実に作成する
"""

import json
import os
import mysql.connector
from datetime import datetime
import logging
from collections import defaultdict
import time

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('complete_jockey_knowledge.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class CompleteJockeyKnowledgeBuilder:
    def __init__(self):
        self.connection = None
        self.jockey_data = {}
        self.processed_jockeys = set()
        self.error_jockeys = set()
        
    def connect_db(self):
        """データベース接続"""
        try:
            self.connection = mysql.connector.connect(
                host='172.25.160.1',
                user='root',
                password='admin',
                database='keiba_dw',
                charset='utf8mb4',
                collation='utf8mb4_general_ci'
            )
            logging.info("データベース接続成功")
            return True
        except Exception as e:
            logging.error(f"データベース接続エラー: {e}")
            return False
    
    def load_existing_data(self):
        """既存の中間ファイルからデータを読み込み"""
        loaded_count = 0
        
        # 中間ファイルから読み込み
        for i in range(1, 101):
            filename = f'data/jockey_knowledge_intermediate_{i}.json'
            if os.path.exists(filename):
                try:
                    with open(filename, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        for jockey_name, jockey_info in data.items():
                            # 有効なデータのみ読み込み
                            if jockey_info.get('overall_stats', {}).get('total_races_analyzed', 0) > 0:
                                self.jockey_data[jockey_name] = jockey_info
                                self.processed_jockeys.add(jockey_name)
                                loaded_count += 1
                except Exception as e:
                    logging.error(f"中間ファイル読み込みエラー {filename}: {e}")
        
        logging.info(f"既存データ読み込み完了: {loaded_count}騎手")
        return loaded_count
    
    def get_all_jockeys(self):
        """全騎手リストを取得（エラー回避版）"""
        cursor = self.connection.cursor()
        
        # KISHUMEI_RYAKUSHOカラムを使用（エラーの原因となるカラムは使わない）
        query = """
        SELECT DISTINCT KISHUMEI_RYAKUSHO
        FROM keiba_dw.jra_race_result
        WHERE KISHUMEI_RYAKUSHO IS NOT NULL 
        AND KISHUMEI_RYAKUSHO != ''
        AND LENGTH(TRIM(KISHUMEI_RYAKUSHO)) > 0
        ORDER BY KISHUMEI_RYAKUSHO
        """
        
        try:
            cursor.execute(query)
            jockeys = [row[0] for row in cursor.fetchall()]
            logging.info(f"全騎手リスト取得完了: {len(jockeys)}名")
            return jockeys
        except Exception as e:
            logging.error(f"騎手リスト取得エラー: {e}")
            return []
        finally:
            cursor.close()
    
    def get_jockey_basic_stats(self, jockey_name):
        """騎手の基本統計（簡略版）"""
        cursor = self.connection.cursor()
        
        # エラーの原因となるカラムを除外したクエリ
        query = """
        SELECT 
            COUNT(*) as total_races,
            SUM(CASE WHEN TRIM(KAKUTEIJYUNI) = '1' THEN 1 ELSE 0 END) as wins,
            SUM(CASE WHEN TRIM(KAKUTEIJYUNI) <= '3' THEN 1 ELSE 0 END) as fukusho
        FROM keiba_dw.jra_race_result
        WHERE KISHUMEI_RYAKUSHO = %s
        """
        
        try:
            cursor.execute(query, (jockey_name,))
            result = cursor.fetchone()
            
            if result:
                total, wins, fukusho = result
                return {
                    'total_races': int(total),
                    'wins': int(wins) if wins else 0,
                    'fukusho': int(fukusho) if fukusho else 0,
                    'win_rate': round((wins / total * 100) if total > 0 and wins else 0, 1),
                    'fukusho_rate': round((fukusho / total * 100) if total > 0 and fukusho else 0, 1)
                }
        except Exception as e:
            logging.error(f"基本統計取得エラー({jockey_name}): {e}")
        finally:
            cursor.close()
        
        return None
    
    def process_remaining_jockeys(self):
        """未処理の騎手を処理"""
        all_jockeys = self.get_all_jockeys()
        remaining_jockeys = [j for j in all_jockeys if j not in self.processed_jockeys]
        
        logging.info(f"未処理騎手数: {len(remaining_jockeys)}")
        
        for idx, jockey_name in enumerate(remaining_jockeys, 1):
            try:
                logging.info(f"処理中 ({idx}/{len(remaining_jockeys)}): {jockey_name}")
                
                # 基本統計のみ取得（エラーを避けるため）
                basic_stats = self.get_jockey_basic_stats(jockey_name)
                
                if basic_stats:
                    self.jockey_data[jockey_name] = {
                        'name': jockey_name,
                        'overall_stats': basic_stats,
                        'processed_at': datetime.now().isoformat()
                    }
                    self.processed_jockeys.add(jockey_name)
                else:
                    self.error_jockeys.add(jockey_name)
                
                # 10騎手ごとに中間保存
                if idx % 10 == 0:
                    self.save_final_data()
                    
            except Exception as e:
                logging.error(f"騎手処理エラー({jockey_name}): {e}")
                self.error_jockeys.add(jockey_name)
            
            # 負荷軽減
            time.sleep(0.1)
    
    def save_final_data(self):
        """最終データを保存"""
        # メインファイル
        json_filename = "data/jockey_knowledge.json"
        with open(json_filename, "w", encoding="utf-8") as f:
            json.dump(self.jockey_data, f, ensure_ascii=False, indent=2)
        
        # サマリーファイル
        summary_filename = "data/jockey_knowledge_summary.txt"
        with open(summary_filename, "w", encoding="utf-8") as f:
            f.write(f"=== 騎手ナレッジファイル完全版 ===\n")
            f.write(f"作成日時: {datetime.now()}\n")
            f.write(f"総騎手数: {len(self.jockey_data)}\n")
            f.write(f"エラー騎手数: {len(self.error_jockeys)}\n")
            f.write(f"\n=== 収録騎手一覧 ===\n")
            for name in sorted(self.jockey_data.keys()):
                stats = self.jockey_data[name].get('overall_stats', {})
                f.write(f"{name} - {stats.get('total_races', 0)}戦 "
                       f"勝率{stats.get('win_rate', 0)}% "
                       f"複勝率{stats.get('fukusho_rate', 0)}%\n")
        
        logging.info(f"保存完了: {json_filename} ({len(self.jockey_data)}騎手)")
    
    def run(self):
        """メイン処理"""
        logging.info("=== 騎手ナレッジファイル完全版作成開始 ===")
        
        # データベース接続
        if not self.connect_db():
            return
        
        try:
            # 既存データ読み込み
            existing_count = self.load_existing_data()
            
            # 残りの騎手を処理
            self.process_remaining_jockeys()
            
            # 最終保存
            self.save_final_data()
            
            logging.info(f"=== 処理完了 ===")
            logging.info(f"総騎手数: {len(self.jockey_data)}")
            logging.info(f"エラー騎手数: {len(self.error_jockeys)}")
            
        finally:
            if self.connection:
                self.connection.close()

if __name__ == "__main__":
    builder = CompleteJockeyKnowledgeBuilder()
    builder.run()