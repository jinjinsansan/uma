#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
騎手ナレッジファイル完全版作成スクリプト
1. 既存の504騎手の完全データを保持
2. 残り567騎手を正しいSQLで処理
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
        logging.FileHandler('merge_and_complete.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class MergeAndCompleteJockeyKnowledge:
    def __init__(self):
        self.connection = None
        self.jockey_data = {}
        self.processed_jockeys = set()
        
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
    
    def load_existing_data(self):
        """既存の中間ファイルから完全データを読み込み"""
        loaded_count = 0
        valid_count = 0
        
        # 中間ファイルから読み込み（1-50まで確実に存在）
        for i in range(1, 101):
            filename = f'data/jockey_knowledge_intermediate_{i}.json'
            if os.path.exists(filename):
                try:
                    with open(filename, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        for jockey_name, jockey_info in data.items():
                            # 完全なデータ構造を持つ騎手のみ
                            if (jockey_info.get('overall_stats', {}).get('total_races_analyzed', 0) > 0 and
                                'venue_course_stats' in jockey_info and
                                'track_condition_stats' in jockey_info):
                                self.jockey_data[jockey_name] = jockey_info
                                self.processed_jockeys.add(jockey_name)
                                valid_count += 1
                            loaded_count += 1
                except Exception as e:
                    logging.error(f"中間ファイル読み込みエラー {filename}: {e}")
        
        logging.info(f"既存データ読み込み完了: {valid_count}/{loaded_count}騎手（有効/総数）")
        return valid_count
    
    def get_all_jockeys(self):
        """2015-2025年の全騎手リストを取得"""
        cursor = self.connection.cursor()
        
        query = """
        SELECT DISTINCT KISHUMEI_RYAKUSHO
        FROM umagoto_race_joho
        WHERE KISHUMEI_RYAKUSHO IS NOT NULL 
        AND KISHUMEI_RYAKUSHO != ''
        AND LENGTH(TRIM(KISHUMEI_RYAKUSHO)) > 0
        AND KAISAI_NEN >= '2015'
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
    
    def get_jockey_venue_course_results(self, jockey_name):
        """騎手の競馬場・距離別成績（v3.pyからコピー、エラーカラムを修正）"""
        cursor = self.connection.cursor()
        
        query = """
        SELECT 
            u.KAISAI_NEN, u.KAISAI_GAPPI, u.KEIBAJO_CODE,
            u.KAKUTEI_CHAKUJUN, u.NYUSEN_JUNI,
            r.KYORI, u.BAMEI
        FROM umagoto_race_joho u
        LEFT JOIN race_shosai r 
            ON u.RACE_CODE = r.RACE_CODE
        WHERE u.KISHUMEI_RYAKUSHO = %s
        AND u.KAISAI_NEN >= '2015'
        AND u.KAKUTEI_CHAKUJUN IS NOT NULL
        AND u.KAKUTEI_CHAKUJUN != ''
        AND u.KAKUTEI_CHAKUJUN != '00'
        ORDER BY u.KAISAI_NEN DESC, u.KAISAI_GAPPI DESC
        """
        
        try:
            cursor.execute(query, (jockey_name,))
            all_results = cursor.fetchall()
        except Exception as e:
            logging.error(f"競馬場別成績取得エラー({jockey_name}): {e}")
            return {}
        finally:
            cursor.close()
        
        # 競馬場・距離別に分類
        venue_results = defaultdict(list)
        jyo_map = {
            '01': '札幌', '02': '函館', '03': '福島', '04': '新潟',
            '05': '東京', '06': '中山', '07': '中京', '08': '京都',
            '09': '阪神', '10': '小倉'
        }
        
        for result in all_results:
            year, date, keibajo_code, position, entry_count, distance, horse_name = result
            
            try:
                pos = int(position)
                if pos == 0 or pos > 18:
                    continue
            except:
                continue
            
            venue_name = jyo_map.get(keibajo_code, f'不明({keibajo_code})')
            key = f"{venue_name}_{distance}"
            
            if len(venue_results[key]) < 5:
                venue_results[key].append({
                    'date': f"{year}-{date}",
                    'horse_name': horse_name,
                    'position': pos,
                    'total_horses': int(entry_count) if entry_count else 18,
                    'is_fukusho': pos <= 3
                })
        
        # 複勝率を計算
        venue_course_stats = {}
        for key, results in venue_results.items():
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
        """騎手の馬場状態別成績"""
        cursor = self.connection.cursor()
        
        query = """
        SELECT 
            u.KAISAI_NEN, u.KAISAI_GAPPI,
            u.KAKUTEI_CHAKUJUN, u.NYUSEN_JUNI,
            r.TRACK_CODE, u.BAMEI
        FROM umagoto_race_joho u
        LEFT JOIN race_shosai r 
            ON u.RACE_CODE = r.RACE_CODE
        WHERE u.KISHUMEI_RYAKUSHO = %s
        AND u.KAISAI_NEN >= '2015'
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
        finally:
            cursor.close()
        
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
        """騎手の枠順別成績"""
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
        finally:
            cursor.close()
        
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
        """騎手の種牡馬別成績（エラーカラムを使わない）"""
        cursor = self.connection.cursor()
        
        query = """
        SELECT 
            u.KAISAI_NEN, u.KAISAI_GAPPI, k.KETTO1_BAMEI,
            u.KAKUTEI_CHAKUJUN, u.NYUSEN_JUNI, u.BAMEI
        FROM umagoto_race_joho u
        LEFT JOIN kyosoba_master2 k 
            ON u.KETTO_TOROKU_BANGO = k.KETTO_TOROKU_BANGO
        WHERE u.KISHUMEI_RYAKUSHO = %s
        AND u.KAISAI_NEN >= '2015'
        AND u.KAKUTEI_CHAKUJUN IS NOT NULL
        AND u.KAKUTEI_CHAKUJUN != ''
        AND u.KAKUTEI_CHAKUJUN != '00'
        AND k.KETTO1_BAMEI IS NOT NULL
        ORDER BY u.KAISAI_NEN DESC, u.KAISAI_GAPPI DESC
        """
        
        try:
            cursor.execute(query, (jockey_name,))
            all_results = cursor.fetchall()
        except Exception as e:
            logging.error(f"種牡馬別成績取得エラー({jockey_name}): {e}")
            return {}
        finally:
            cursor.close()
        
        # 種牡馬別に分類
        sire_results = defaultdict(list)
        for result in all_results:
            year, date, sire_name, position, entry_count, horse_name = result
            
            if not sire_name:
                continue
            
            try:
                pos = int(position)
                if pos == 0 or pos > 18:
                    continue
            except:
                continue
            
            if len(sire_results[sire_name]) < 5:
                sire_results[sire_name].append({
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
        logging.info(f"処理中: {jockey_name}")
        
        try:
            # 各種成績を取得
            venue_course_stats = self.get_jockey_venue_course_results(jockey_name)
            track_condition_stats = self.get_jockey_track_condition_results(jockey_name)
            post_position_stats = self.get_jockey_post_position_results(jockey_name)
            sire_stats = self.get_jockey_sire_results(jockey_name)
            
            # 全体統計を計算
            total_races = 0
            total_fukusho = 0
            
            for stats_dict in [venue_course_stats, track_condition_stats, 
                             post_position_stats, sire_stats]:
                for key, stats in stats_dict.items():
                    results = stats.get('results', [])
                    total_races += len(results)
                    total_fukusho += sum(1 for r in results if r['is_fukusho'])
            
            overall_stats = {
                'total_races_analyzed': total_races,
                'overall_fukusho_rate': round((total_fukusho / total_races * 100) if total_races > 0 else 0, 1)
            }
            
            # データを保存
            self.jockey_data[jockey_name] = {
                'name': jockey_name,
                'venue_course_stats': venue_course_stats,
                'track_condition_stats': track_condition_stats,
                'post_position_stats': post_position_stats,
                'sire_stats': sire_stats,
                'processed_at': datetime.now().isoformat(),
                'overall_stats': overall_stats
            }
            
            return True
            
        except Exception as e:
            logging.error(f"騎手処理エラー({jockey_name}): {e}")
            return False
    
    def process_remaining_jockeys(self):
        """未処理の騎手を処理"""
        all_jockeys = self.get_all_jockeys()
        remaining_jockeys = [j for j in all_jockeys if j not in self.processed_jockeys]
        
        logging.info(f"未処理騎手数: {len(remaining_jockeys)}")
        
        success_count = 0
        error_count = 0
        
        for idx, jockey_name in enumerate(remaining_jockeys, 1):
            if self.process_jockey(jockey_name):
                success_count += 1
            else:
                error_count += 1
            
            # 10騎手ごとに保存
            if idx % 10 == 0:
                self.save_final_data()
                logging.info(f"進捗: {idx}/{len(remaining_jockeys)} (成功: {success_count}, エラー: {error_count})")
            
            # 負荷軽減
            time.sleep(0.5)
        
        return success_count, error_count
    
    def save_final_data(self):
        """最終データを保存"""
        # メインファイル
        json_filename = "data/jockey_knowledge.json"
        with open(json_filename, "w", encoding="utf-8") as f:
            json.dump(self.jockey_data, f, ensure_ascii=False, indent=2)
        
        # サマリーファイル
        summary_filename = "data/jockey_knowledge_summary.txt"
        with open(summary_filename, "w", encoding="utf-8") as f:
            f.write(f"=== 騎手ナレッジファイル ===\n")
            f.write(f"作成日時: {datetime.now()}\n")
            f.write(f"騎手数: {len(self.jockey_data)}\n")
            f.write(f"\n=== 収録騎手一覧 ===\n")
            
            for name in sorted(self.jockey_data.keys()):
                stats = self.jockey_data[name].get('overall_stats', {})
                f.write(f"{name} - 分析レース数: {stats.get('total_races_analyzed', 0)}, "
                       f"複勝率: {stats.get('overall_fukusho_rate', 0)}%\n")
        
        logging.info(f"保存完了: {json_filename} ({len(self.jockey_data)}騎手)")
    
    def run(self):
        """メイン処理"""
        logging.info("=== 騎手ナレッジファイルマージ&完成処理開始 ===")
        
        # データベース接続
        if not self.connect_db():
            return
        
        try:
            # 既存データ読み込み
            existing_count = self.load_existing_data()
            logging.info(f"既存の完全データ: {existing_count}騎手")
            
            # 残りの騎手を処理
            success, error = self.process_remaining_jockeys()
            
            # 最終保存
            self.save_final_data()
            
            logging.info(f"=== 処理完了 ===")
            logging.info(f"総騎手数: {len(self.jockey_data)}")
            logging.info(f"新規処理成功: {success}")
            logging.info(f"新規処理エラー: {error}")
            
        finally:
            if self.connection:
                self.connection.close()

if __name__ == "__main__":
    merger = MergeAndCompleteJockeyKnowledge()
    merger.run()