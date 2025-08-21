#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
騎手ナレッジファイル9レース版作成スクリプト
社長の要望に応えて、各統計で直近9レースを取得する
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
        logging.FileHandler('jockey_9races_process.log'),
        logging.StreamHandler()
    ]
)

# データベース接続設定
DB_CONFIG = {
    'host': '172.25.160.1',
    'user': 'root',
    'password': '04050405Aoi-',
    'database': 'mykeibadb'
}

# 定数：9レースに変更
RACES_LIMIT = 9  # 社長の要望通り9レースを取得

class JockeyKnowledgeBuilder:
    def __init__(self):
        self.connection = mysql.connector.connect(**DB_CONFIG)
        self.all_jockeys = []
        
    def get_all_jockeys(self):
        """2015年～2025年に騎乗した全騎手を取得"""
        cursor = self.connection.cursor()
        
        query = """
        SELECT DISTINCT KISHUMEI_RYAKUSHO
        FROM umagoto_race_joho
        WHERE KAISAI_NEN >= '2015'
        AND KAISAI_NEN <= '2025'
        AND KISHUMEI_RYAKUSHO IS NOT NULL
        AND KISHUMEI_RYAKUSHO != ''
        ORDER BY KISHUMEI_RYAKUSHO
        """
        
        try:
            cursor.execute(query)
            results = cursor.fetchall()
            self.all_jockeys = [row[0] for row in results]
            logging.info(f"騎手総数: {len(self.all_jockeys)}")
        except Exception as e:
            logging.error(f"騎手一覧取得エラー: {e}")
            self.all_jockeys = []
        finally:
            cursor.close()
    
    def get_jockey_venue_course_results(self, jockey_name):
        """騎手の競馬場・距離別成績（直近9レース）"""
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
            
            # 9レースまで取得（社長の要望）
            if len(venue_results[key]) < RACES_LIMIT:
                venue_results[key].append({
                    'date': f"{year}-{date}",  # シンプルな日付形式
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
        """騎手の馬場状態別成績（直近9レース）"""
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
            
            # 9レースまで取得（社長の要望）
            if len(track_results[track_name]) < RACES_LIMIT:
                track_results[track_name].append({
                    'date': f"{year}-{date}",
                    'horse_name': horse_name,
                    'position': pos,
                    'total_horses': int(entry_count) if entry_count else 18,
                    'is_fukusho': pos <= 3
                })
        
        # 複勝率を計算
        track_condition_stats = {}
        for track_name, results in track_results.items():
            if results:
                fukusho_count = sum(1 for r in results if r['is_fukusho'])
                fukusho_rate = fukusho_count / len(results) * 100
                track_condition_stats[track_name] = {
                    'results': results,
                    'fukusho_rate': round(fukusho_rate, 1),
                    'race_count': len(results)
                }
        
        return track_condition_stats
    
    def get_jockey_post_position_results(self, jockey_name):
        """騎手の枠順別成績（直近9レース）"""
        cursor = self.connection.cursor()
        
        query = """
        SELECT 
            u.KAISAI_NEN, u.KAISAI_GAPPI,
            u.KAKUTEI_CHAKUJUN, u.NYUSEN_JUNI,
            u.WAKUBAN, u.BAMEI
        FROM umagoto_race_joho u
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
            logging.error(f"枠順別成績取得エラー({jockey_name}): {e}")
            return {}
        finally:
            cursor.close()
        
        # 枠順別に分類
        post_results = defaultdict(list)
        
        for result in all_results:
            year, date, position, entry_count, wakuban, horse_name = result
            
            try:
                pos = int(position)
                if pos == 0 or pos > 18:
                    continue
            except:
                continue
            
            try:
                waku = int(wakuban) if wakuban else 0
                if waku == 0:
                    continue
            except:
                continue
            
            waku_key = f"枠{waku}"
            
            # 9レースまで取得（社長の要望）
            if len(post_results[waku_key]) < RACES_LIMIT:
                post_results[waku_key].append({
                    'date': f"{year}-{date}",
                    'horse_name': horse_name,
                    'position': pos,
                    'total_horses': int(entry_count) if entry_count else 18,
                    'is_fukusho': pos <= 3
                })
        
        # 複勝率を計算
        post_position_stats = {}
        for waku_key, results in post_results.items():
            if results:
                fukusho_count = sum(1 for r in results if r['is_fukusho'])
                fukusho_rate = fukusho_count / len(results) * 100
                post_position_stats[waku_key] = {
                    'results': results,
                    'fukusho_rate': round(fukusho_rate, 1),
                    'race_count': len(results)
                }
        
        return post_position_stats
    
    def get_jockey_sire_results(self, jockey_name):
        """騎手の種牡馬別成績（直近9レース）"""
        cursor = self.connection.cursor()
        
        query = """
        SELECT 
            u.KAISAI_NEN, u.KAISAI_GAPPI,
            u.KAKUTEI_CHAKUJUN, u.NYUSEN_JUNI,
            h.FATHER_UMA_NAME, u.BAMEI
        FROM umagoto_race_joho u
        LEFT JOIN horse_profile h 
            ON u.KETTONUM = h.KETTONUM
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
            logging.error(f"種牡馬別成績取得エラー({jockey_name}): {e}")
            return {}
        finally:
            cursor.close()
        
        # 種牡馬別に分類
        sire_results = defaultdict(list)
        
        for result in all_results:
            year, date, position, entry_count, sire_name, horse_name = result
            
            if not sire_name:
                continue
                
            try:
                pos = int(position)
                if pos == 0 or pos > 18:
                    continue
            except:
                continue
            
            # 9レースまで取得（社長の要望）
            if len(sire_results[sire_name]) < RACES_LIMIT:
                sire_results[sire_name].append({
                    'date': f"{year}-{date}",
                    'horse_name': horse_name,
                    'position': pos,
                    'total_horses': int(entry_count) if entry_count else 18,
                    'is_fukusho': pos <= 3
                })
        
        # 複勝率を計算
        sire_stats = {}
        for sire_name, results in sire_results.items():
            if results:
                fukusho_count = sum(1 for r in results if r['is_fukusho'])
                fukusho_rate = fukusho_count / len(results) * 100
                sire_stats[sire_name] = {
                    'results': results,
                    'fukusho_rate': round(fukusho_rate, 1),
                    'race_count': len(results)
                }
        
        return sire_stats
    
    def process_single_jockey(self, jockey_name):
        """単一騎手のデータを処理"""
        logging.info(f"処理中: {jockey_name}")
        
        jockey_data = {
            'name': jockey_name.strip(),  # 末尾スペースを削除
            'venue_course_stats': self.get_jockey_venue_course_results(jockey_name),
            'track_condition_stats': self.get_jockey_track_condition_results(jockey_name),
            'post_position_stats': self.get_jockey_post_position_results(jockey_name),
            'sire_stats': self.get_jockey_sire_results(jockey_name),
            'processed_at': datetime.now().isoformat()
        }
        
        # 総合統計を計算
        total_races = 0
        total_fukusho = 0
        
        # すべての統計から集計
        for stats_type in ['venue_course_stats', 'track_condition_stats', 
                          'post_position_stats', 'sire_stats']:
            for key, data in jockey_data[stats_type].items():
                if 'results' in data:
                    races = len(data['results'])
                    fukusho = sum(1 for r in data['results'] if r['is_fukusho'])
                    total_races += races
                    total_fukusho += fukusho
        
        # 重複を考慮して調整（概算）
        unique_races = total_races // 4  # 4つの統計で重複するため
        unique_fukusho = total_fukusho // 4
        
        overall_fukusho_rate = (unique_fukusho / unique_races * 100) if unique_races > 0 else 0
        
        jockey_data['overall_stats'] = {
            'total_races_analyzed': unique_races,
            'overall_fukusho_rate': round(overall_fukusho_rate, 1)
        }
        
        return jockey_data
    
    def build_knowledge(self):
        """全騎手のナレッジを構築"""
        self.get_all_jockeys()
        
        all_knowledge = {}
        success_count = 0
        error_count = 0
        
        for i, jockey_name in enumerate(self.all_jockeys):
            try:
                jockey_data = self.process_single_jockey(jockey_name)
                # 騎手名は末尾スペースを含む元の形で保存
                all_knowledge[jockey_name] = jockey_data
                success_count += 1
                
                # 10騎手ごとに保存
                if (i + 1) % 10 == 0:
                    self.save_knowledge(all_knowledge)
                    logging.info(f"保存完了: data/jockey_knowledge_9races.json ({len(all_knowledge)}騎手)")
                
                # 進捗表示
                if (i + 1) % 50 == 0:
                    logging.info(f"進捗: {i + 1}/{len(self.all_jockeys)} (成功: {success_count}, エラー: {error_count})")
                
                # 1騎手処理したら少し待機（DB負荷軽減）
                time.sleep(0.5)
                
            except Exception as e:
                logging.error(f"騎手処理エラー({jockey_name}): {e}")
                error_count += 1
        
        # 最終保存
        self.save_knowledge(all_knowledge)
        
        logging.info("=== 処理完了 ===")
        logging.info(f"総騎手数: {len(all_knowledge)}")
        logging.info(f"処理成功: {success_count}")
        logging.info(f"処理エラー: {error_count}")
        
        return all_knowledge
    
    def save_knowledge(self, knowledge_data):
        """ナレッジデータを保存"""
        output_dir = 'data'
        os.makedirs(output_dir, exist_ok=True)
        
        output_file = os.path.join(output_dir, 'jockey_knowledge_9races.json')
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(knowledge_data, f, ensure_ascii=False, indent=2)
    
    def close(self):
        """データベース接続を閉じる"""
        if self.connection:
            self.connection.close()

if __name__ == "__main__":
    logging.info("騎手ナレッジファイル9レース版作成開始")
    logging.info(f"各統計で直近{RACES_LIMIT}レースを取得します")
    
    builder = JockeyKnowledgeBuilder()
    try:
        builder.build_knowledge()
    finally:
        builder.close()
    
    logging.info("処理が完了しました")