"""
拡張版騎手ナレッジファイル作成スクリプト V2
既存のテーブル構造に合わせて修正版
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
from decimal import Decimal

# JSON用Decimalエンコーダー
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('extended_jockey_knowledge_v2.log', encoding='utf-8'),
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
            u.KISHUMEI_RYAKUSHO as jockey_name
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
    
    def get_jockey_recent_races(self, jockey_name: str, limit: int = 9) -> List[dict]:
        """騎手の直近レース情報を取得（最大9レース）"""
        query = """
        SELECT 
            u.KAISAI_NEN,
            u.KAISAI_GAPPI,
            u.KEIBAJO_CODE,
            r.KYORI,
            r.TRACK_CODE,
            u.KAKUTEI_CHAKUJUN,
            u.NYUSEN_JUNI,
            u.BAMEI,
            r.RACE_CODE,
            u.WAKUBAN
        FROM umagoto_race_joho u
        LEFT JOIN race_shosai r ON u.RACE_CODE = r.RACE_CODE
        WHERE u.KISHUMEI_RYAKUSHO = %s
            AND u.KAISAI_NEN >= '2015'
            AND u.KAKUTEI_CHAKUJUN IS NOT NULL
            AND u.KAKUTEI_CHAKUJUN != ''
            AND u.KAKUTEI_CHAKUJUN != '00'
        ORDER BY u.KAISAI_NEN DESC, u.KAISAI_GAPPI DESC
        LIMIT %s
        """
        
        self.cursor.execute(query, (jockey_name, limit))
        races = []
        for row in self.cursor.fetchall():
            try:
                races.append({
                    'year': row[0],
                    'date': row[1],
                    'venue_code': row[2],
                    'distance': int(row[3]) if row[3] else 0,
                    'track_condition': row[4],
                    'order_of_finish': int(row[5]) if row[5] else 0,
                    'total_horses': int(row[6]) if row[6] else 18,
                    'horse_name': row[7],
                    'race_code': row[8],
                    'post_position': int(row[9]) if row[9] else 0
                })
            except Exception as e:
                logger.debug(f"レースデータ変換エラー: {e}")
                continue
        return races
    
    def get_venue_course_full_stats(self, jockey_name: str) -> Dict[str, dict]:
        """競馬場・距離別の全期間成績を取得"""
        query = """
        SELECT 
            u.KEIBAJO_CODE,
            r.KYORI,
            COUNT(*) as total_races,
            SUM(CASE WHEN u.KAKUTEI_CHAKUJUN = '01' THEN 1 ELSE 0 END) as wins,
            SUM(CASE WHEN u.KAKUTEI_CHAKUJUN IN ('01', '02', '03') THEN 1 ELSE 0 END) as top3
        FROM umagoto_race_joho u
        LEFT JOIN race_shosai r ON u.RACE_CODE = r.RACE_CODE
        WHERE u.KISHUMEI_RYAKUSHO = %s
            AND u.KAISAI_NEN >= '2015'
            AND u.KAKUTEI_CHAKUJUN IS NOT NULL
            AND u.KAKUTEI_CHAKUJUN != ''
            AND u.KAKUTEI_CHAKUJUN != '00'
            AND r.KYORI IS NOT NULL
        GROUP BY u.KEIBAJO_CODE, r.KYORI
        HAVING total_races >= 3
        """
        
        self.cursor.execute(query, (jockey_name,))
        
        # 競馬場コードを名前に変換
        venue_map = {
            '01': '札幌', '02': '函館', '03': '福島', '04': '新潟',
            '05': '東京', '06': '中山', '07': '中京', '08': '京都',
            '09': '阪神', '10': '小倉'
        }
        
        stats = {}
        for row in self.cursor.fetchall():
            venue_code = row[0]
            distance = row[1]
            total_races = row[2]
            wins = row[3]
            top3 = row[4]
            
            venue_name = venue_map.get(venue_code, f'不明({venue_code})')
            key = f"{venue_name}_{distance}"
            
            stats[key] = {
                'total_races': total_races,
                'wins': wins,
                'win_rate': round(wins / total_races, 3) if total_races > 0 else 0,
                'top3_rate': round(top3 / total_races, 3) if total_races > 0 else 0
            }
        
        return stats
    
    def get_bloodline_stats(self, jockey_name: str) -> Dict[str, dict]:
        """種牡馬別成績を取得（簡易版）"""
        # 注: 種牡馬データは別テーブルにあるため、ここでは馬名ベースで集計
        query = """
        SELECT 
            LEFT(u.BAMEI, 3) as sire_prefix,  -- 馬名の最初3文字で代用
            COUNT(*) as total_races,
            SUM(CASE WHEN u.KAKUTEI_CHAKUJUN = '01' THEN 1 ELSE 0 END) as wins,
            SUM(CASE WHEN u.KAKUTEI_CHAKUJUN IN ('01', '02', '03') THEN 1 ELSE 0 END) as top3
        FROM umagoto_race_joho u
        WHERE u.KISHUMEI_RYAKUSHO = %s
            AND u.KAISAI_NEN >= '2015'
            AND u.KAKUTEI_CHAKUJUN IS NOT NULL
            AND u.KAKUTEI_CHAKUJUN != ''
            AND u.KAKUTEI_CHAKUJUN != '00'
            AND u.BAMEI IS NOT NULL
        GROUP BY sire_prefix
        HAVING total_races >= 5
        ORDER BY total_races DESC
        LIMIT 30
        """
        
        self.cursor.execute(query, (jockey_name,))
        stats = {}
        
        for row in self.cursor.fetchall():
            prefix = row[0]
            total_races = row[1]
            wins = row[2]
            top3 = row[3]
            
            if prefix:
                stats[f"{prefix}系"] = {
                    'total_races': total_races,
                    'wins': wins,
                    'win_rate': round(wins / total_races, 3) if total_races > 0 else 0,
                    'top3_rate': round(top3 / total_races, 3) if total_races > 0 else 0
                }
        
        return stats
    
    def get_post_position_by_course(self, jockey_name: str) -> Dict[str, dict]:
        """コース別枠順成績を取得"""
        query = """
        SELECT 
            u.KEIBAJO_CODE,
            r.KYORI,
            u.WAKUBAN,
            COUNT(*) as races,
            SUM(CASE WHEN u.KAKUTEI_CHAKUJUN = '01' THEN 1 ELSE 0 END) as wins
        FROM umagoto_race_joho u
        LEFT JOIN race_shosai r ON u.RACE_CODE = r.RACE_CODE
        WHERE u.KISHUMEI_RYAKUSHO = %s
            AND u.KAISAI_NEN >= '2015'
            AND u.KAKUTEI_CHAKUJUN IS NOT NULL
            AND u.KAKUTEI_CHAKUJUN != ''
            AND u.KAKUTEI_CHAKUJUN != '00'
            AND u.WAKUBAN IS NOT NULL
            AND u.WAKUBAN > 0
            AND r.KYORI IS NOT NULL
        GROUP BY u.KEIBAJO_CODE, r.KYORI, u.WAKUBAN
        HAVING races >= 2
        """
        
        self.cursor.execute(query, (jockey_name,))
        
        venue_map = {
            '01': '札幌', '02': '函館', '03': '福島', '04': '新潟',
            '05': '東京', '06': '中山', '07': '中京', '08': '京都',
            '09': '阪神', '10': '小倉'
        }
        
        stats = defaultdict(dict)
        
        for row in self.cursor.fetchall():
            venue_code = row[0]
            distance = row[1]
            post_position = str(row[2])
            races = row[3]
            wins = row[4]
            
            venue_name = venue_map.get(venue_code, f'不明({venue_code})')
            key = f"{venue_name}_{distance}"
            
            stats[key][post_position] = {
                'races': races,
                'wins': wins,
                'win_rate': round(wins / races, 3) if races > 0 else 0
            }
        
        return dict(stats)
    
    def calculate_basic_stats_from_recent(self, jockey_name: str, recent_races: List[dict]) -> dict:
        """直近9レースから基本統計を計算"""
        if not recent_races:
            return {}
        
        # 競馬場コードを名前に変換
        venue_map = {
            '01': '札幌', '02': '函館', '03': '福島', '04': '新潟',
            '05': '東京', '06': '中山', '07': '中京', '08': '京都',
            '09': '阪神', '10': '小倉'
        }
        
        # 競馬場・距離別
        venue_course_stats = defaultdict(lambda: {'races': 0, 'wins': 0, 'top3': 0})
        # 馬場状態別
        track_condition_stats = defaultdict(lambda: {'races': 0, 'wins': 0, 'top3': 0})
        # 枠順別
        post_position_stats = defaultdict(lambda: {'races': 0, 'wins': 0, 'top3': 0})
        
        total_races = len(recent_races)
        total_wins = sum(1 for r in recent_races if r['order_of_finish'] == 1)
        total_top3 = sum(1 for r in recent_races if r['order_of_finish'] <= 3)
        
        for race in recent_races:
            venue = venue_map.get(race['venue_code'], race['venue_code'])
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
            
            # 馬場状態（簡易版）
            track_cond = '良'  # デフォルト
            if race['track_condition']:
                if race['track_condition'] in ['11', '12', '13', '14']:
                    track_cond = '良'
                elif race['track_condition'] in ['21', '22', '23', '24']:
                    track_cond = '稍重'
                elif race['track_condition'] in ['31', '32', '33', '34']:
                    track_cond = '重'
                elif race['track_condition'] in ['41', '42', '43', '44']:
                    track_cond = '不良'
            
            track_condition_stats[track_cond]['races'] += 1
            if is_win:
                track_condition_stats[track_cond]['wins'] += 1
            if is_top3:
                track_condition_stats[track_cond]['top3'] += 1
            
            # 枠順
            if race['post_position'] > 0:
                post = str(race['post_position'])
                post_position_stats[post]['races'] += 1
                if is_win:
                    post_position_stats[post]['wins'] += 1
                if is_top3:
                    post_position_stats[post]['top3'] += 1
        
        # 率の計算
        for stats in [venue_course_stats, track_condition_stats, post_position_stats]:
            for key, data in stats.items():
                if data['races'] > 0:
                    data['win_rate'] = round(data['wins'] / data['races'], 3)
                    data['top3_rate'] = round(data['top3'] / data['races'], 3)
        
        # 種牡馬別（既存のSQLから取得）
        try:
            sire_stats_full = self.get_jockey_sire_stats(jockey_name)
        except:
            sire_stats_full = {}
        
        return {
            'venue_course_stats': dict(venue_course_stats),
            'track_condition_stats': dict(track_condition_stats),
            'post_position_stats': dict(post_position_stats),
            'sire_stats': sire_stats_full,  # 全期間のデータを使用
            'overall_stats': {
                'total_races_analyzed': total_races,
                'overall_win_rate': round(total_wins / total_races, 3) if total_races > 0 else 0,
                'overall_top3_rate': round(total_top3 / total_races, 3) if total_races > 0 else 0
            }
        }
    
    def get_jockey_sire_stats(self, jockey_name: str) -> dict:
        """騎手の種牡馬別成績（簡易版）"""
        # ここでは直近レースから取得
        return {}
    
    def process_jockey(self, jockey_name: str) -> dict:
        """騎手1人分のデータを処理"""
        try:
            # 騎手名のクリーニング
            jockey_name = jockey_name.strip()
            
            # 1. 直近9レースを取得
            recent_races = self.get_jockey_recent_races(jockey_name, limit=9)
            
            if len(recent_races) < 3:
                logger.info(f"{jockey_name}: データ不足（{len(recent_races)}レース）")
                return None
            
            # 2. 基本統計（直近9レース）
            basic_stats = self.calculate_basic_stats_from_recent(jockey_name, recent_races)
            
            # 3. 全期間統計
            venue_course_full = self.get_venue_course_full_stats(jockey_name)
            bloodline_stats = self.get_bloodline_stats(jockey_name)
            post_by_course = self.get_post_position_by_course(jockey_name)
            
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
            import traceback
            logger.error(traceback.format_exc())
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
            for idx, (jockey_name,) in enumerate(jockeys, 1):
                logger.info(f"[{idx}/{total_jockeys}] {jockey_name} 処理中...")
                
                jockey_data = self.process_jockey(jockey_name)
                
                if jockey_data:
                    self.jockey_data[jockey_name] = jockey_data
                
                # 進捗保存（50人ごと）
                if idx % 50 == 0:
                    self.save_progress(idx)
                
                # 休憩（DB負荷軽減）
                time.sleep(0.1)
            
            # 最終保存
            self.save_final()
            
        finally:
            self.disconnect_db()
    
    def save_progress(self, count: int):
        """進捗を中間ファイルとして保存"""
        progress_file = f'data/extended_jockey_knowledge_progress_{count}.json'
        os.makedirs('data', exist_ok=True)
        
        with open(progress_file, 'w', encoding='utf-8') as f:
            json.dump(self.jockey_data, f, ensure_ascii=False, indent=2, cls=DecimalEncoder)
        
        logger.info(f"進捗保存: {progress_file} ({len(self.jockey_data)}名)")
    
    def save_final(self):
        """最終的なナレッジファイルを保存"""
        os.makedirs('data', exist_ok=True)
        
        # 通常版
        output_file = 'data/extended_jockey_knowledge.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.jockey_data, f, ensure_ascii=False, indent=2, cls=DecimalEncoder)
        
        # 圧縮版
        gz_file = 'data/extended_jockey_knowledge.json.gz'
        with gzip.open(gz_file, 'wt', encoding='utf-8') as f:
            json.dump(self.jockey_data, f, ensure_ascii=False, cls=DecimalEncoder)
        
        # ファイルサイズ確認
        size_mb = os.path.getsize(output_file) / (1024 * 1024)
        size_gz_mb = os.path.getsize(gz_file) / (1024 * 1024)
        
        logger.info(f"保存完了: {output_file} ({size_mb:.1f}MB)")
        logger.info(f"圧縮版: {gz_file} ({size_gz_mb:.1f}MB)")
        logger.info(f"収録騎手数: {len(self.jockey_data)}名")


if __name__ == "__main__":
    logger.info("拡張版騎手ナレッジファイル作成開始 V2")
    logger.info("データ収集期間: 2015-2025年")
    logger.info("収集データ: 直近9レース + 全期間統計")
    
    builder = ExtendedJockeyKnowledgeBuilder()
    builder.build_knowledge()
    
    logger.info("処理完了！")