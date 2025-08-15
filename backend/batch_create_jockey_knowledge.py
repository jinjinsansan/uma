"""
騎手ナレッジファイル作成バッチ処理
2010年～2025年のJRA全騎手の成績データを収集

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

class JockeyKnowledgeBuilder:
    def __init__(self):
        self.connection = None
        self.jockey_data = {}
        self.start_time = time.time()
        
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
            print("データベース接続成功")
            return True
        except Error as e:
            print(f"データベース接続エラー: {e}")
            return False
    
    def get_all_jockeys(self):
        """2010年～2025年の全騎手リストを取得"""
        cursor = self.connection.cursor()
        
        query = """
        SELECT DISTINCT kishumei
        FROM n_uma_race
        WHERE year >= 2010 
        AND year <= 2025
        AND kishumei IS NOT NULL
        AND kishumei != ''
        ORDER BY kishumei
        """
        
        cursor.execute(query)
        jockeys = [row[0] for row in cursor.fetchall()]
        print(f"対象騎手数: {len(jockeys)}")
        return jockeys
    
    def get_jockey_venue_course_results(self, jockey_name):
        """騎手の開催地別・コース別成績（直近5回）"""
        cursor = self.connection.cursor()
        
        query = """
        SELECT 
            year, monthday, jyocd, kyori,
            kakuteijyuni, tosu
        FROM n_uma_race
        WHERE kishumei = %s
        AND year >= 2010
        AND kakuteijyuni IS NOT NULL
        AND kakuteijyuni > 0
        ORDER BY year DESC, monthday DESC
        """
        
        cursor.execute(query, (jockey_name,))
        all_results = cursor.fetchall()
        
        # 開催地・距離別に分類
        venue_course_results = defaultdict(list)
        for result in all_results:
            year, monthday, jyocd, kyori, position, tosu = result
            venue_distance_key = f"{jyocd}_{kyori}"
            
            if len(venue_course_results[venue_distance_key]) < 5:
                venue_course_results[venue_distance_key].append({
                    'date': f"{year}-{monthday}",
                    'position': position,
                    'total_horses': tosu,
                    'is_fukusho': position <= 3  # 3着以内
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
        
        query = """
        SELECT 
            year, monthday, trackcd,
            kakuteijyuni, tosu
        FROM n_uma_race
        WHERE kishumei = %s
        AND year >= 2010
        AND kakuteijyuni IS NOT NULL
        AND kakuteijyuni > 0
        AND trackcd IS NOT NULL
        ORDER BY year DESC, monthday DESC
        """
        
        cursor.execute(query, (jockey_name,))
        all_results = cursor.fetchall()
        
        # 馬場状態別に分類
        track_results = defaultdict(list)
        track_map = {'1': '良', '2': '稍重', '3': '重', '4': '不良'}
        
        for result in all_results:
            year, monthday, trackcd, position, tosu = result
            track_name = track_map.get(str(trackcd), f'不明({trackcd})')
            
            if len(track_results[track_name]) < 5:
                track_results[track_name].append({
                    'date': f"{year}-{monthday}",
                    'position': position,
                    'total_horses': tosu,
                    'is_fukusho': position <= 3
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
            year, monthday, wakuban,
            kakuteijyuni, tosu
        FROM n_uma_race
        WHERE kishumei = %s
        AND year >= 2010
        AND kakuteijyuni IS NOT NULL
        AND kakuteijyuni > 0
        AND wakuban IS NOT NULL
        AND wakuban > 0
        ORDER BY year DESC, monthday DESC
        """
        
        cursor.execute(query, (jockey_name,))
        all_results = cursor.fetchall()
        
        # 枠番別に分類
        post_results = defaultdict(list)
        for result in all_results:
            year, monthday, wakuban, position, tosu = result
            
            if len(post_results[wakuban]) < 5:
                post_results[wakuban].append({
                    'date': f"{year}-{monthday}",
                    'position': position,
                    'total_horses': tosu,
                    'is_fukusho': position <= 3
                })
        
        # 複勝率を計算
        post_stats = {}
        for post, results in post_results.items():
            if results:
                fukusho_count = sum(1 for r in results if r['is_fukusho'])
                fukusho_rate = fukusho_count / len(results) * 100
                post_stats[f"枠{post}"] = {
                    'results': results,
                    'fukusho_rate': round(fukusho_rate, 1),
                    'race_count': len(results)
                }
        
        return post_stats
    
    def get_jockey_sire_results(self, jockey_name):
        """騎手の種牡馬別成績（直近5回）"""
        cursor = self.connection.cursor()
        
        query = """
        SELECT 
            year, monthday, father,
            kakuteijyuni, tosu, bamei
        FROM n_uma_race
        WHERE kishumei = %s
        AND year >= 2010
        AND kakuteijyuni IS NOT NULL
        AND kakuteijyuni > 0
        AND father IS NOT NULL
        AND father != ''
        ORDER BY year DESC, monthday DESC
        """
        
        cursor.execute(query, (jockey_name,))
        all_results = cursor.fetchall()
        
        # 種牡馬別に分類
        sire_results = defaultdict(list)
        for result in all_results:
            year, monthday, father, position, tosu, bamei = result
            
            if len(sire_results[father]) < 5:
                sire_results[father].append({
                    'date': f"{year}-{monthday}",
                    'horse_name': bamei,
                    'position': position,
                    'total_horses': tosu,
                    'is_fukusho': position <= 3
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
                    for result in data['results']:
                        total_races += 1
                        if result['is_fukusho']:
                            total_fukusho += 1
        
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
                print(f"\n処理中 ({idx + 1}/{len(jockeys)}): {jockey_name}")
                
                try:
                    jockey_data = self.process_jockey(jockey_name)
                    self.jockey_data[jockey_name] = jockey_data
                    
                    # 進捗を記録
                    with open(progress_file, "a", encoding="utf-8") as f:
                        f.write(f"{datetime.now().isoformat()} - 処理完了: {jockey_name}\n")
                    
                    # 10人ごとに中間保存
                    if (idx + 1) % 10 == 0:
                        self.save_intermediate_data(idx + 1)
                        
                except Exception as e:
                    print(f"  エラー: {jockey_name} - {e}")
                    continue
                
                # 処理速度の調整
                time.sleep(0.1)
            
            # 最終的なファイルを保存
            self.save_final_data()
            
        except Exception as e:
            print(f"処理エラー: {e}")
        finally:
            if self.connection and self.connection.is_connected():
                self.connection.close()
    
    def save_intermediate_data(self, count):
        """中間データを保存"""
        filename = f"data/jockey_knowledge_intermediate_{count}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.jockey_data, f, ensure_ascii=False, indent=2)
        print(f"  中間保存完了: {filename}")
    
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
            f.write(f"処理時間: {time.time() - self.start_time:.1f}秒\n\n")
            
            f.write("=== 収録騎手一覧 ===\n")
            for jockey_name in sorted(self.jockey_data.keys()):
                overall_rate = self.jockey_data[jockey_name]['overall_stats']['overall_fukusho_rate']
                f.write(f"{jockey_name} - 総合複勝率: {overall_rate}%\n")
        
        print(f"\n処理完了!")
        print(f"  JSONファイル: {json_filename}")
        print(f"  サマリーファイル: {summary_filename}")
        print(f"  騎手数: {len(self.jockey_data)}")
        print(f"  処理時間: {time.time() - self.start_time:.1f}秒")

if __name__ == "__main__":
    builder = JockeyKnowledgeBuilder()
    builder.build_knowledge_file()