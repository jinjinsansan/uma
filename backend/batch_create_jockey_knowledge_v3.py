"""
騎手ナレッジファイル作成バッチ処理 v3
2010年～2025年のJRA全騎手の成績データを収集
テーブル名とカラム名を修正版

収集データ:
1. 開催地別・コース別成績（直近5回）
2. 馬場状態別成績（直近5回）
3. 枠順別成績（直近5回）
4. 種牡馬別成績（直近5回）

各データから複勝率（3着以内率）を計算
"""

import mysql.connector
from mysql.connector import Error
import json
from datetime import datetime
import time
from collections import defaultdict
import os
import logging

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/jockey_knowledge_batch.log'),
        logging.StreamHandler()
    ]
)

class JockeyKnowledgeBuilder:
    def __init__(self):
        self.connection = None
        self.jockey_data = {}
        self.start_time = time.time()
        self.processed_count = 0
        self.error_count = 0
        
    def connect_to_database(self):
        """MySQLデータベースに接続"""
        try:
            self.connection = mysql.connector.connect(
                host='172.25.160.1',
                database='mykeibadb',
                user='root',
                password='04050405Aoi-',
                port=3306,
                charset='utf8mb4'
            )
            logging.info("データベース接続成功")
            return True
        except Error as e:
            logging.error(f"データベース接続エラー: {e}")
            return False
    
    def get_all_jockeys(self):
        """2010年～2025年の全騎手リストを取得"""
        cursor = self.connection.cursor()
        
        # まずテーブル名を確認
        query = """
        SELECT DISTINCT KISHUMEI_RYAKUSHO
        FROM umagoto_race_joho
        WHERE KAISAI_NEN >= '2010' 
        AND KAISAI_NEN <= '2025'
        AND KISHUMEI_RYAKUSHO IS NOT NULL
        AND KISHUMEI_RYAKUSHO != ''
        AND KISHUMEI_RYAKUSHO != '不明'
        ORDER BY KISHUMEI_RYAKUSHO
        """
        
        try:
            cursor.execute(query)
            jockeys = [row[0] for row in cursor.fetchall()]
            logging.info(f"対象騎手数: {len(jockeys)}")
            return jockeys
        except Exception as e:
            logging.error(f"騎手リスト取得エラー: {e}")
            return []
    
    def get_jockey_venue_course_results(self, jockey_name):
        """騎手の開催地別・コース別成績（直近5回）"""
        cursor = self.connection.cursor()
        
        # まず、race_shosaiテーブルから距離情報を取得する必要がある
        query = """
        SELECT 
            u.KAISAI_NEN, u.KAISAI_GAPPI, u.KEIBAJO_CODE,
            u.KAKUTEI_CHAKUJUN, u.NYUSEN_JUNI,
            r.KYORI, u.BAMEI
        FROM umagoto_race_joho u
        LEFT JOIN race_shosai r 
            ON u.RACE_CODE = r.RACE_CODE
        WHERE u.KISHUMEI_RYAKUSHO = %s
        AND u.KAISAI_NEN >= '2010'
        AND u.KAKUTEI_CHAKUJUN IS NOT NULL
        AND u.KAKUTEI_CHAKUJUN != ''
        AND u.KAKUTEI_CHAKUJUN != '00'
        ORDER BY u.KAISAI_NEN DESC, u.KAISAI_GAPPI DESC
        """
        
        try:
            cursor.execute(query, (jockey_name,))
            all_results = cursor.fetchall()
        except Exception as e:
            logging.error(f"開催地別成績取得エラー({jockey_name}): {e}")
            return {}
        
        # 開催地・距離別に分類
        venue_course_results = defaultdict(list)
        
        # 場所コードマッピング
        venue_map = {
            '01': '札幌', '02': '函館', '03': '福島', '04': '新潟',
            '05': '東京', '06': '中山', '07': '中京', '08': '京都',
            '09': '阪神', '10': '小倉'
        }
        
        for result in all_results:
            year, date, venue_code, position, entry_count, distance, horse_name = result
            if not distance:
                continue
                
            venue_name = venue_map.get(venue_code, venue_code)
            venue_distance_key = f"{venue_name}_{distance}m"
            
            # 着順を数値に変換
            try:
                pos = int(position)
                if pos == 0 or pos > 18:  # 00は未出走、18着以下は除外
                    continue
            except:
                continue
            
            if len(venue_course_results[venue_distance_key]) < 5:
                venue_course_results[venue_distance_key].append({
                    'date': f"{year}-{date}",
                    'horse_name': horse_name,
                    'position': pos,
                    'total_horses': int(entry_count) if entry_count else 18,
                    'is_fukusho': pos <= 3  # 3着以内
                })
        
        # 複勝率を計算
        venue_course_stats = {}
        for key, results in venue_course_results.items():
            if results:
                fukusho_count = sum(1 for r in results if r['is_fukusho'])
                fukusho_rate = fukusho_count / len(results) * 100
                venue_course_stats[key] = {
                    'results': results,
                    'fukusho_rate': round(fukusho_rate, 1),
                    'race_count': len(results)
                }
        
        return venue_course_stats
    
    def get_jockey_track_condition_results(self, jockey_name):
        """騎手の馬場状態別成績（直近5回）"""
        cursor = self.connection.cursor()
        
        # race_shosaiテーブルから馬場状態を取得
        query = """
        SELECT 
            u.KAISAI_NEN, u.KAISAI_GAPPI,
            u.KAKUTEI_CHAKUJUN, u.NYUSEN_JUNI,
            r.TRACK_CODE, u.BAMEI
        FROM umagoto_race_joho u
        LEFT JOIN race_shosai r 
            ON u.RACE_CODE = r.RACE_CODE
        WHERE u.KISHUMEI_RYAKUSHO = %s
        AND u.KAISAI_NEN >= '2010'
        AND u.KAKUTEI_CHAKUJUN IS NOT NULL
        AND u.KAKUTEI_CHAKUJUN != ''
        AND u.KAKUTEI_CHAKUJUN != '00'
        ORDER BY u.KAISAI_NEN DESC, u.KAISAI_GAPPI DESC
        """
        
        try:
            cursor.execute(query, (jockey_name,))
            all_results = cursor.fetchall()
        except Exception as e:
            logging.error(f"馬場状態別成績取得エラー({jockey_name}): {e}")
            return {}
        
        # 馬場状態別に分類
        track_results = defaultdict(list)
        track_map = {'1': '良', '2': '稍重', '3': '重', '4': '不良'}
        
        for result in all_results:
            year, date, position, entry_count, track_code, horse_name = result
            if not track_code:
                continue
                
            track_name = track_map.get(track_code, f'不明({track_code})')
            
            try:
                pos = int(position)
                if pos == 0 or pos > 18:
                    continue
            except:
                continue
            
            if len(track_results[track_name]) < 5:
                track_results[track_name].append({
                    'date': f"{year}-{date}",
                    'horse_name': horse_name,
                    'position': pos,
                    'total_horses': int(entry_count) if entry_count else 18,
                    'is_fukusho': pos <= 3
                })
        
        # 複勝率を計算
        track_stats = {}
        for track, results in track_results.items():
            if results:
                fukusho_count = sum(1 for r in results if r['is_fukusho'])
                fukusho_rate = fukusho_count / len(results) * 100
                track_stats[track] = {
                    'results': results,
                    'fukusho_rate': round(fukusho_rate, 1),
                    'race_count': len(results)
                }
        
        return track_stats
    
    def get_jockey_post_position_results(self, jockey_name):
        """騎手の枠順別成績（直近5回）"""
        cursor = self.connection.cursor()
        
        query = """
        SELECT 
            KAISAI_NEN, KAISAI_GAPPI, WAKUBAN,
            KAKUTEI_CHAKUJUN, NYUSEN_JUNI, BAMEI
        FROM umagoto_race_joho
        WHERE KISHUMEI_RYAKUSHO = %s
        AND KAISAI_NEN >= '2010'
        AND KAKUTEI_CHAKUJUN IS NOT NULL
        AND KAKUTEI_CHAKUJUN != ''
        AND KAKUTEI_CHAKUJUN != '00'
        AND WAKUBAN IS NOT NULL
        AND WAKUBAN != ''
        ORDER BY KAISAI_NEN DESC, KAISAI_GAPPI DESC
        """
        
        try:
            cursor.execute(query, (jockey_name,))
            all_results = cursor.fetchall()
        except Exception as e:
            logging.error(f"枠順別成績取得エラー({jockey_name}): {e}")
            return {}
        
        # 枠番別に分類
        post_results = defaultdict(list)
        for result in all_results:
            year, date, wakuban, position, entry_count, horse_name = result
            
            try:
                pos = int(position)
                if pos == 0 or pos > 18:
                    continue
            except:
                continue
            
            waku_key = f"枠{wakuban}"
            
            if len(post_results[waku_key]) < 5:
                post_results[waku_key].append({
                    'date': f"{year}-{date}",
                    'horse_name': horse_name,
                    'position': pos,
                    'total_horses': int(entry_count) if entry_count else 18,
                    'is_fukusho': pos <= 3
                })
        
        # 複勝率を計算
        post_stats = {}
        for post, results in post_results.items():
            if results:
                fukusho_count = sum(1 for r in results if r['is_fukusho'])
                fukusho_rate = fukusho_count / len(results) * 100
                post_stats[post] = {
                    'results': results,
                    'fukusho_rate': round(fukusho_rate, 1),
                    'race_count': len(results)
                }
        
        return post_stats
    
    def get_jockey_sire_results(self, jockey_name):
        """騎手の種牡馬別成績（直近5回）"""
        cursor = self.connection.cursor()
        
        # kyosoba_master2テーブルから父馬名を取得（KETTO1_BAMEI使用）
        query = """
        SELECT 
            u.KAISAI_NEN, u.KAISAI_GAPPI, k.KETTO1_BAMEI,
            u.KAKUTEI_CHAKUJUN, u.NYUSEN_JUNI, u.BAMEI
        FROM umagoto_race_joho u
        LEFT JOIN kyosoba_master2 k
            ON u.KETTO_TOROKU_BANGO = k.KETTO_TOROKU_BANGO
        WHERE u.KISHUMEI_RYAKUSHO = %s
        AND u.KAISAI_NEN >= '2010'
        AND u.KAKUTEI_CHAKUJUN IS NOT NULL
        AND u.KAKUTEI_CHAKUJUN != ''
        AND u.KAKUTEI_CHAKUJUN != '00'
        ORDER BY u.KAISAI_NEN DESC, u.KAISAI_GAPPI DESC
        """
        
        try:
            cursor.execute(query, (jockey_name,))
            all_results = cursor.fetchall()
        except Exception as e:
            logging.error(f"種牡馬別成績取得エラー({jockey_name}): {e}")
            return {}
        
        # 種牡馬別に分類
        sire_results = defaultdict(list)
        for result in all_results:
            year, date, father_name, position, entry_count, horse_name = result
            if not father_name:
                continue
            
            try:
                pos = int(position)
                if pos == 0 or pos > 18:
                    continue
            except:
                continue
            
            if len(sire_results[father_name]) < 5:
                sire_results[father_name].append({
                    'date': f"{year}-{date}",
                    'horse_name': horse_name,
                    'position': pos,
                    'total_horses': int(entry_count) if entry_count else 18,
                    'is_fukusho': pos <= 3
                })
        
        # 複勝率を計算
        sire_stats = {}
        for sire, results in sire_results.items():
            if results:
                fukusho_count = sum(1 for r in results if r['is_fukusho'])
                fukusho_rate = fukusho_count / len(results) * 100
                sire_stats[sire] = {
                    'results': results,
                    'fukusho_rate': round(fukusho_rate, 1),
                    'race_count': len(results)
                }
        
        return sire_stats
    
    def process_jockey(self, jockey_name):
        """騎手の全データを処理"""
        jockey_info = {
            'name': jockey_name,
            'venue_course_stats': self.get_jockey_venue_course_results(jockey_name),
            'track_condition_stats': self.get_jockey_track_condition_results(jockey_name),
            'post_position_stats': self.get_jockey_post_position_results(jockey_name),
            'sire_stats': self.get_jockey_sire_results(jockey_name),
            'processed_at': datetime.now().isoformat()
        }
        
        # 総合統計を計算
        total_races = 0
        total_fukusho = 0
        
        for stats_type in ['venue_course_stats', 'track_condition_stats', 'post_position_stats', 'sire_stats']:
            for key, data in jockey_info[stats_type].items():
                if 'results' in data:
                    # 重複を避けるため、最初の統計タイプのみカウント
                    if stats_type == 'venue_course_stats':
                        total_races += len(data['results'])
                        total_fukusho += sum(1 for r in data['results'] if r['is_fukusho'])
        
        overall_fukusho_rate = round(total_fukusho / total_races * 100, 1) if total_races > 0 else 0
        
        jockey_info['overall_stats'] = {
            'total_races_analyzed': total_races,
            'overall_fukusho_rate': overall_fukusho_rate
        }
        
        return jockey_info
    
    def build_knowledge_file(self):
        """全騎手のナレッジファイルを作成"""
        if not self.connect_to_database():
            return
        
        try:
            # 全騎手リストを取得
            jockeys = self.get_all_jockeys()
            
            # 進捗ファイル
            progress_file = "data/jockey_knowledge_progress.txt"
            os.makedirs("data", exist_ok=True)
            
            # 各騎手のデータを処理
            for idx, jockey_name in enumerate(jockeys):
                logging.info(f"処理中 ({idx + 1}/{len(jockeys)}): {jockey_name}")
                
                try:
                    jockey_data = self.process_jockey(jockey_name)
                    self.jockey_data[jockey_name] = jockey_data
                    self.processed_count += 1
                    
                    # 進捗を記録
                    with open(progress_file, "a", encoding="utf-8") as f:
                        f.write(f"{datetime.now().isoformat()} - 処理完了: {jockey_name}\n")
                    
                    # 10人ごとに中間保存
                    if (idx + 1) % 10 == 0:
                        self.save_intermediate_data(idx + 1)
                        
                except Exception as e:
                    logging.error(f"エラー: {jockey_name} - {e}")
                    self.error_count += 1
                    continue
                
                # 処理速度の調整
                time.sleep(0.1)
            
            # 最終的なファイルを保存
            self.save_final_data()
            
        except Exception as e:
            logging.error(f"処理エラー: {e}")
        finally:
            if self.connection and self.connection.is_connected():
                self.connection.close()
    
    def save_intermediate_data(self, count):
        """中間データを保存"""
        filename = f"data/jockey_knowledge_intermediate_{count}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.jockey_data, f, ensure_ascii=False, indent=2)
        logging.info(f"中間保存完了: {filename}")
    
    def save_final_data(self):
        """最終データを保存"""
        # JSONファイル
        json_filename = "data/jockey_knowledge.json"
        with open(json_filename, "w", encoding="utf-8") as f:
            json.dump(self.jockey_data, f, ensure_ascii=False, indent=2)
        
        # サマリーファイル
        summary_filename = "data/jockey_knowledge_summary.txt"
        with open(summary_filename, "w", encoding="utf-8") as f:
            f.write("=== 騎手ナレッジファイル サマリー ===\n")
            f.write(f"作成日時: {datetime.now().isoformat()}\n")
            f.write(f"騎手数: {len(self.jockey_data)}\n")
            f.write(f"正常処理数: {self.processed_count}\n")
            f.write(f"エラー数: {self.error_count}\n")
            f.write(f"処理時間: {time.time() - self.start_time:.1f}秒\n\n")
            
            f.write("=== 収録騎手一覧 ===\n")
            for jockey_name in sorted(self.jockey_data.keys()):
                overall_rate = self.jockey_data[jockey_name]['overall_stats']['overall_fukusho_rate']
                f.write(f"{jockey_name} - 総合複勝率: {overall_rate}%\n")
        
        logging.info(f"\n処理完了!")
        logging.info(f"  JSONファイル: {json_filename}")
        logging.info(f"  サマリーファイル: {summary_filename}")
        logging.info(f"  騎手数: {len(self.jockey_data)}")
        logging.info(f"  正常処理数: {self.processed_count}")
        logging.info(f"  エラー数: {self.error_count}")
        logging.info(f"  処理時間: {time.time() - self.start_time:.1f}秒")

if __name__ == "__main__":
    builder = JockeyKnowledgeBuilder()
    builder.build_knowledge_file()