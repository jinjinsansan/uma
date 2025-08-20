"""
拡張版騎手ナレッジファイル作成スクリプト
過去9回分のデータを収集し、コース別成績・血統別成績・枠順別成績を含む
"""
import json
import os
import pymysql
import logging
from datetime import datetime, date
from collections import defaultdict
import time
from typing import Dict, List, Any
import gzip

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('extended_jockey_knowledge.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# データベース接続設定
DB_CONFIG = {
    'host': '172.25.160.1',
    'user': 'root',
    'password': '04050405Aoi-',
    'database': 'mykeibadb',
    'charset': 'utf8mb4'
}

class ExtendedJockeyKnowledgeBuilder:
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.jockey_data = {}
        self.progress_count = 0
        
    def connect_db(self):
        """データベース接続"""
        try:
            self.conn = pymysql.connect(**DB_CONFIG)
            self.cursor = self.conn.cursor()
            logger.info("データベース接続成功")
        except Exception as e:
            logger.error(f"データベース接続エラー: {e}")
            raise
    
    def disconnect_db(self):
        """データベース切断"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        logger.info("データベース切断")
    
    def get_active_jockeys(self) -> List[tuple]:
        """2015年以降に騎乗した騎手リストを取得"""
        query = """
        SELECT DISTINCT 
            u.KISHUMEI_RYAKUSHO as jockey_name,
            u.KISHUMEI_RYAKUSHO as jockey_code
        FROM umagoto_race_joho u
        WHERE u.KAISAI_NEN >= '2015'
            AND u.KISHUMEI_RYAKUSHO IS NOT NULL
            AND u.KISHUMEI_RYAKUSHO != ''
            AND u.KAKUTEI_CHAKUJUN IS NOT NULL
            AND u.KAKUTEI_CHAKUJUN != ''
            AND u.KAKUTEI_CHAKUJUN != '00'
        GROUP BY u.KISHUMEI_RYAKUSHO
        ORDER BY u.KISHUMEI_RYAKUSHO
        """
        
        self.cursor.execute(query)
        jockeys = self.cursor.fetchall()
        logger.info(f"アクティブ騎手数: {len(jockeys)}名")
        return jockeys
    
    def get_jockey_recent_races(self, jockey_code: str, limit: int = 9) -> List[dict]:
        """騎手の直近レース情報を取得（最大9レース）"""
        query = """
        SELECT 
            ri.race_key,
            ri.race_date,
            ri.race_name,
            ri.track_code,
            ri.distance,
            ri.track_type,
            ri.track_condition,
            ri.race_class,
            rr.horse_number,
            rr.post_position,
            rr.order_of_finish,
            rr.odds,
            rr.popularity,
            hd.horse_name,
            hd.sire_name,
            hd.mare_name
        FROM race_result rr
        INNER JOIN race_info ri ON rr.race_key = ri.race_key
        INNER JOIN horse_data hd ON rr.horse_id = hd.horse_id
        WHERE rr.jockey_code = %s
            AND ri.race_date >= '2015-01-01'
            AND rr.order_of_finish IS NOT NULL
            AND rr.order_of_finish > 0
        ORDER BY ri.race_date DESC, ri.race_number DESC
        LIMIT %s
        """
        
        self.cursor.execute(query, (jockey_code, limit))
        races = []
        for row in self.cursor.fetchall():
            races.append({
                'race_key': row[0],
                'race_date': row[1],
                'race_name': row[2],
                'track_code': row[3],
                'distance': row[4],
                'track_type': row[5],
                'track_condition': row[6],
                'race_class': row[7],
                'horse_number': row[8],
                'post_position': row[9],
                'order_of_finish': row[10],
                'odds': float(row[11]) if row[11] else 0,
                'popularity': row[12],
                'horse_name': row[13],
                'sire_name': row[14],
                'mare_name': row[15]
            })
        return races
    
    def get_venue_course_full_stats(self, jockey_code: str) -> Dict[str, dict]:
        """競馬場・距離別の全期間成績を取得"""
        query = """
        SELECT 
            CONCAT(
                CASE ri.track_code
                    WHEN '01' THEN '札幌'
                    WHEN '02' THEN '函館'
                    WHEN '03' THEN '福島'
                    WHEN '04' THEN '新潟'
                    WHEN '05' THEN '東京'
                    WHEN '06' THEN '中山'
                    WHEN '07' THEN '中京'
                    WHEN '08' THEN '京都'
                    WHEN '09' THEN '阪神'
                    WHEN '10' THEN '小倉'
                    ELSE ri.track_code
                END,
                '_',
                ri.distance
            ) as venue_distance,
            COUNT(*) as total_races,
            SUM(CASE WHEN rr.order_of_finish = 1 THEN 1 ELSE 0 END) as wins,
            SUM(CASE WHEN rr.order_of_finish <= 3 THEN 1 ELSE 0 END) as top3
        FROM race_result rr
        INNER JOIN race_info ri ON rr.race_key = ri.race_key
        WHERE rr.jockey_code = %s
            AND ri.race_date >= '2015-01-01'
            AND rr.order_of_finish IS NOT NULL
            AND rr.order_of_finish > 0
        GROUP BY venue_distance
        HAVING total_races >= 3
        """
        
        self.cursor.execute(query, (jockey_code,))
        stats = {}
        for row in self.cursor.fetchall():
            venue_distance = row[0]
            total_races = row[1]
            wins = row[2]
            top3 = row[3]
            
            stats[venue_distance] = {
                'total_races': total_races,
                'wins': wins,
                'win_rate': round(wins / total_races, 3) if total_races > 0 else 0,
                'top3_rate': round(top3 / total_races, 3) if total_races > 0 else 0
            }
        
        return stats
    
    def get_bloodline_stats(self, jockey_code: str) -> Dict[str, dict]:
        """種牡馬別成績を取得"""
        query = """
        SELECT 
            hd.sire_name,
            COUNT(*) as total_races,
            SUM(CASE WHEN rr.order_of_finish = 1 THEN 1 ELSE 0 END) as wins,
            SUM(CASE WHEN rr.order_of_finish <= 3 THEN 1 ELSE 0 END) as top3
        FROM race_result rr
        INNER JOIN race_info ri ON rr.race_key = ri.race_key
        INNER JOIN horse_data hd ON rr.horse_id = hd.horse_id
        WHERE rr.jockey_code = %s
            AND ri.race_date >= '2015-01-01'
            AND rr.order_of_finish IS NOT NULL
            AND rr.order_of_finish > 0
            AND hd.sire_name IS NOT NULL
            AND hd.sire_name != ''
        GROUP BY hd.sire_name
        HAVING total_races >= 5
        ORDER BY total_races DESC
        LIMIT 50
        """
        
        self.cursor.execute(query, (jockey_code,))
        stats = {}
        for row in self.cursor.fetchall():
            sire_name = row[0]
            total_races = row[1]
            wins = row[2]
            top3 = row[3]
            
            stats[sire_name] = {
                'total_races': total_races,
                'wins': wins,
                'win_rate': round(wins / total_races, 3) if total_races > 0 else 0,
                'top3_rate': round(top3 / total_races, 3) if total_races > 0 else 0
            }
        
        return stats
    
    def get_post_position_by_course(self, jockey_code: str) -> Dict[str, dict]:
        """コース別枠順成績を取得"""
        query = """
        SELECT 
            CONCAT(
                CASE ri.track_code
                    WHEN '01' THEN '札幌'
                    WHEN '02' THEN '函館'
                    WHEN '03' THEN '福島'
                    WHEN '04' THEN '新潟'
                    WHEN '05' THEN '東京'
                    WHEN '06' THEN '中山'
                    WHEN '07' THEN '中京'
                    WHEN '08' THEN '京都'
                    WHEN '09' THEN '阪神'
                    WHEN '10' THEN '小倉'
                    ELSE ri.track_code
                END,
                '_',
                ri.distance
            ) as venue_distance,
            rr.post_position,
            COUNT(*) as races,
            SUM(CASE WHEN rr.order_of_finish = 1 THEN 1 ELSE 0 END) as wins
        FROM race_result rr
        INNER JOIN race_info ri ON rr.race_key = ri.race_key
        WHERE rr.jockey_code = %s
            AND ri.race_date >= '2015-01-01'
            AND rr.order_of_finish IS NOT NULL
            AND rr.order_of_finish > 0
            AND rr.post_position IS NOT NULL
            AND rr.post_position > 0
        GROUP BY venue_distance, rr.post_position
        HAVING races >= 2
        """
        
        self.cursor.execute(query, (jockey_code,))
        stats = defaultdict(dict)
        
        for row in self.cursor.fetchall():
            venue_distance = row[0]
            post_position = str(row[1])
            races = row[2]
            wins = row[3]
            
            stats[venue_distance][post_position] = {
                'races': races,
                'wins': wins,
                'win_rate': round(wins / races, 3) if races > 0 else 0
            }
        
        return dict(stats)
    
    def calculate_basic_stats_from_recent(self, recent_races: List[dict]) -> dict:
        """直近9レースから基本統計を計算"""
        if not recent_races:
            return {}
        
        # 競馬場・距離別
        venue_course_stats = defaultdict(lambda: {'races': 0, 'wins': 0, 'top3': 0})
        # 馬場状態別
        track_condition_stats = defaultdict(lambda: {'races': 0, 'wins': 0, 'top3': 0})
        # 枠順別
        post_position_stats = defaultdict(lambda: {'races': 0, 'wins': 0, 'top3': 0})
        # 種牡馬別（直近）
        sire_stats = defaultdict(lambda: {'races': 0, 'wins': 0, 'top3': 0})
        
        total_races = len(recent_races)
        total_wins = sum(1 for r in recent_races if r['order_of_finish'] == 1)
        total_top3 = sum(1 for r in recent_races if r['order_of_finish'] <= 3)
        
        for race in recent_races:
            # 競馬場コードを名前に変換
            venue_map = {
                '01': '札幌', '02': '函館', '03': '福島', '04': '新潟',
                '05': '東京', '06': '中山', '07': '中京', '08': '京都',
                '09': '阪神', '10': '小倉'
            }
            venue = venue_map.get(race['track_code'], race['track_code'])
            venue_distance = f"{venue}_{race['distance']}"
            
            # 統計更新
            is_win = race['order_of_finish'] == 1
            is_top3 = race['order_of_finish'] <= 3
            
            # 競馬場・距離
            venue_course_stats[venue_distance]['races'] += 1
            if is_win:
                venue_course_stats[venue_distance]['wins'] += 1
            if is_top3:
                venue_course_stats[venue_distance]['top3'] += 1
            
            # 馬場状態
            track_cond = race['track_condition'] or '良'
            track_condition_stats[track_cond]['races'] += 1
            if is_win:
                track_condition_stats[track_cond]['wins'] += 1
            if is_top3:
                track_condition_stats[track_cond]['top3'] += 1
            
            # 枠順
            if race['post_position']:
                post = str(race['post_position'])
                post_position_stats[post]['races'] += 1
                if is_win:
                    post_position_stats[post]['wins'] += 1
                if is_top3:
                    post_position_stats[post]['top3'] += 1
            
            # 種牡馬
            if race['sire_name']:
                sire_stats[race['sire_name']]['races'] += 1
                if is_win:
                    sire_stats[race['sire_name']]['wins'] += 1
                if is_top3:
                    sire_stats[race['sire_name']]['top3'] += 1
        
        # 率の計算
        for stats in [venue_course_stats, track_condition_stats, post_position_stats, sire_stats]:
            for key, data in stats.items():
                if data['races'] > 0:
                    data['win_rate'] = round(data['wins'] / data['races'], 3)
                    data['top3_rate'] = round(data['top3'] / data['races'], 3)
        
        return {
            'venue_course_stats': dict(venue_course_stats),
            'track_condition_stats': dict(track_condition_stats),
            'post_position_stats': dict(post_position_stats),
            'sire_stats': dict(sire_stats),
            'overall_stats': {
                'total_races_analyzed': total_races,
                'overall_win_rate': round(total_wins / total_races, 3) if total_races > 0 else 0,
                'overall_top3_rate': round(total_top3 / total_races, 3) if total_races > 0 else 0
            }
        }
    
    def process_jockey(self, jockey_code: str, jockey_name: str) -> dict:
        """騎手1人分のデータを処理"""
        try:
            # 1. 直近9レースを取得
            recent_races = self.get_jockey_recent_races(jockey_code, limit=9)
            
            if len(recent_races) < 3:
                logger.info(f"{jockey_name}: データ不足（{len(recent_races)}レース）")
                return None
            
            # 2. 基本統計（直近9レース）
            basic_stats = self.calculate_basic_stats_from_recent(recent_races)
            
            # 3. 全期間統計
            venue_course_full = self.get_venue_course_full_stats(jockey_code)
            bloodline_stats = self.get_bloodline_stats(jockey_code)
            post_by_course = self.get_post_position_by_course(jockey_code)
            
            # 4. データ統合
            jockey_data = {
                **basic_stats,  # 既存の5項目
                'venue_course_full_stats': venue_course_full,
                'bloodline_stats': bloodline_stats,
                'post_position_by_course': post_by_course,
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            logger.info(f"{jockey_name}: 処理完了（全期間: {len(venue_course_full)}コース, 血統: {len(bloodline_stats)}種）")
            return jockey_data
            
        except Exception as e:
            logger.error(f"{jockey_name} 処理エラー: {e}")
            return None
    
    def build_knowledge(self):
        """全騎手のナレッジファイルを構築"""
        try:
            self.connect_db()
            
            # 騎手リスト取得
            jockeys = self.get_active_jockeys()
            total_jockeys = len(jockeys)
            
            logger.info(f"処理開始: {total_jockeys}名の騎手")
            
            # 各騎手を処理
            for idx, (jockey_code, jockey_name) in enumerate(jockeys, 1):
                # 騎手名のクリーニング
                jockey_name = jockey_name.strip()
                
                logger.info(f"[{idx}/{total_jockeys}] {jockey_name} 処理中...")
                
                jockey_data = self.process_jockey(jockey_code, jockey_name)
                
                if jockey_data:
                    self.jockey_data[jockey_name] = jockey_data
                
                # 進捗保存（50人ごと）
                if idx % 50 == 0:
                    self.save_progress(idx)
                
                # 休憩（API負荷軽減）
                time.sleep(0.5)
            
            # 最終保存
            self.save_final()
            
        finally:
            self.disconnect_db()
    
    def save_progress(self, count: int):
        """進捗を中間ファイルとして保存"""
        progress_file = f'data/extended_jockey_knowledge_progress_{count}.json'
        os.makedirs('data', exist_ok=True)
        
        with open(progress_file, 'w', encoding='utf-8') as f:
            json.dump(self.jockey_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"進捗保存: {progress_file} ({len(self.jockey_data)}名)")
    
    def save_final(self):
        """最終的なナレッジファイルを保存"""
        # 通常版
        output_file = 'data/extended_jockey_knowledge.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.jockey_data, f, ensure_ascii=False, indent=2)
        
        # 圧縮版
        gz_file = 'data/extended_jockey_knowledge.json.gz'
        with gzip.open(gz_file, 'wt', encoding='utf-8') as f:
            json.dump(self.jockey_data, f, ensure_ascii=False)
        
        # ファイルサイズ確認
        size_mb = os.path.getsize(output_file) / (1024 * 1024)
        size_gz_mb = os.path.getsize(gz_file) / (1024 * 1024)
        
        logger.info(f"保存完了: {output_file} ({size_mb:.1f}MB)")
        logger.info(f"圧縮版: {gz_file} ({size_gz_mb:.1f}MB)")
        logger.info(f"収録騎手数: {len(self.jockey_data)}名")


if __name__ == "__main__":
    logger.info("拡張版騎手ナレッジファイル作成開始")
    logger.info("データ収集期間: 2015-2025年")
    logger.info("収集データ: 直近9レース + 全期間統計")
    
    builder = ExtendedJockeyKnowledgeBuilder()
    builder.build_knowledge()
    
    logger.info("処理完了！")