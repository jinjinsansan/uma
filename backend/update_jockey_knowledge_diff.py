"""
騎手ナレッジファイル差分更新スクリプト
既存のjockey_knowledge.jsonに新しいレースデータを追加
2024年8月17日以降のデータを取得してマージ

使用方法:
python update_jockey_knowledge_diff.py
"""

import mysql.connector
from mysql.connector import Error
import json
from datetime import datetime, timedelta
import time
from collections import defaultdict
import os
import logging
import gzip
import shutil

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/jockey_knowledge_update.log'),
        logging.StreamHandler()
    ]
)

class JockeyKnowledgeUpdater:
    def __init__(self):
        self.connection = None
        self.existing_data = {}
        self.new_data = {}
        self.start_time = time.time()
        self.update_count = 0
        self.new_jockey_count = 0
        # 更新開始日（8月17日以降のデータを取得）
        self.update_from_date = '2024-08-17'
        
    def connect_to_database(self):
        """MySQLデータベースに接続"""
        try:
            self.connection = mysql.connector.connect(
                host='172.25.160.1',
                database='mykeibadb',  # スクリーンショットで確認したデータベース名
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
    
    def load_existing_knowledge(self):
        """既存の騎手ナレッジファイルを読み込み"""
        file_path = 'data/jockey_knowledge.json'
        
        if not os.path.exists(file_path):
            logging.warning(f"既存ファイルが見つかりません: {file_path}")
            return False
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.existing_data = json.load(f)
            logging.info(f"既存データ読み込み完了: {len(self.existing_data)}騎手")
            return True
        except Exception as e:
            logging.error(f"ファイル読み込みエラー: {e}")
            return False
    
    def get_updated_jockeys(self):
        """更新対象の騎手リストを取得（8月17日以降にレースに騎乗した騎手）"""
        cursor = self.connection.cursor()
        
        # 日付形式を確認するクエリ
        check_query = """
        SELECT DISTINCT 
            KISHUMEI_RYAKUSHO,
            MAX(CONCAT(KAISAI_NEN, '-', KAISAI_GAPPI)) as last_race_date
        FROM umagoto_race_joho
        WHERE CONCAT(KAISAI_NEN, '-', KAISAI_GAPPI) >= %s
        AND KISHUMEI_RYAKUSHO IS NOT NULL
        AND KISHUMEI_RYAKUSHO != ''
        AND KISHUMEI_RYAKUSHO != '不明'
        GROUP BY KISHUMEI_RYAKUSHO
        ORDER BY last_race_date DESC
        """
        
        try:
            # 日付形式を調整（YYYY-MMDD形式）
            update_date = self.update_from_date.replace('-', '')
            cursor.execute(check_query, (update_date,))
            jockeys = cursor.fetchall()
            logging.info(f"更新対象騎手数: {len(jockeys)}")
            for jockey, last_date in jockeys[:5]:  # 最初の5件を表示
                logging.info(f"  {jockey}: 最終騎乗日 {last_date}")
            return [row[0] for row in jockeys]
        except Exception as e:
            logging.error(f"騎手リスト取得エラー: {e}")
            return []
    
    def get_jockey_venue_course_results(self, jockey_name, from_date=None):
        """騎手の開催地別・コース別成績（直近5回）"""
        cursor = self.connection.cursor()
        
        # 日付条件を追加
        date_condition = ""
        if from_date:
            date_condition = f"AND CONCAT(u.KAISAI_NEN, '-', u.KAISAI_GAPPI) >= '{from_date.replace('-', '')}'"
        
        query = f"""
        SELECT 
            u.KAISAI_NEN, u.KAISAI_GAPPI, u.KEIBAJO_CODE,
            u.KAKUTEI_CHAKUJUN, u.NYUSEN_JUNI,
            r.KYORI, u.BAMEI
        FROM umagoto_race_joho u
        LEFT JOIN race_shosai r 
            ON u.RACE_CODE = r.RACE_CODE
        WHERE u.KISHUMEI_RYAKUSHO = %s
        {date_condition}
        AND u.KAKUTEI_CHAKUJUN IS NOT NULL
        AND u.KAKUTEI_CHAKUJUN != ''
        AND u.KAKUTEI_CHAKUJUN != '0'
        AND r.KYORI IS NOT NULL
        ORDER BY u.KAISAI_NEN DESC, u.KAISAI_GAPPI DESC
        """
        
        venue_course_data = defaultdict(lambda: {
            'results': [],
            'fukusho_rate': 0.0,
            'race_count': 0
        })
        
        try:
            cursor.execute(query, (jockey_name,))
            results = cursor.fetchall()
            
            # 開催地コード変換
            venue_map = {
                '01': '札幌', '02': '函館', '03': '福島', '04': '新潟',
                '05': '東京', '06': '中山', '07': '中京', '08': '京都',
                '09': '阪神', '10': '小倉'
            }
            
            for row in results:
                kaisai_nen, kaisai_gappi, keibajo_code, chakujun, juni, kyori, bamei = row
                
                if keibajo_code in venue_map and kyori:
                    venue = venue_map[keibajo_code]
                    course_key = f"{venue}_{kyori}m"
                    
                    # 既存データがあれば最大5件まで保持
                    if len(venue_course_data[course_key]['results']) < 5:
                        try:
                            position = int(chakujun)
                            total = int(juni) if juni else 18
                            is_fukusho = position <= 3
                            
                            venue_course_data[course_key]['results'].append({
                                'date': f"{kaisai_nen}-{kaisai_gappi}",
                                'horse_name': bamei,
                                'position': position,
                                'total_horses': total,
                                'is_fukusho': is_fukusho
                            })
                        except (ValueError, TypeError):
                            continue
            
            # 複勝率計算
            for course_key, data in venue_course_data.items():
                if data['results']:
                    fukusho_count = sum(1 for r in data['results'] if r['is_fukusho'])
                    data['fukusho_rate'] = round((fukusho_count / len(data['results'])) * 100, 1)
                    data['race_count'] = len(data['results'])
            
            return dict(venue_course_data)
            
        except Exception as e:
            logging.error(f"開催地別成績取得エラー ({jockey_name}): {e}")
            return {}
    
    def merge_jockey_data(self, jockey_name, new_venue_data):
        """既存データと新規データをマージ"""
        if jockey_name not in self.existing_data:
            # 新規騎手
            self.existing_data[jockey_name] = {
                'name': jockey_name,
                'venue_course_stats': new_venue_data
            }
            self.new_jockey_count += 1
            logging.info(f"新規騎手追加: {jockey_name}")
        else:
            # 既存騎手のデータ更新
            existing_venue_stats = self.existing_data[jockey_name].get('venue_course_stats', {})
            
            for course_key, new_data in new_venue_data.items():
                if course_key not in existing_venue_stats:
                    # 新しいコース
                    existing_venue_stats[course_key] = new_data
                else:
                    # 既存コースのデータに追加
                    existing_results = existing_venue_stats[course_key].get('results', [])
                    new_results = new_data['results']
                    
                    # 新しい結果を先頭に追加（重複を避ける）
                    existing_dates = {r['date'] for r in existing_results}
                    for result in new_results:
                        if result['date'] not in existing_dates:
                            existing_results.insert(0, result)
                    
                    # 最新5件のみ保持
                    existing_results = existing_results[:5]
                    
                    # 複勝率を再計算
                    if existing_results:
                        fukusho_count = sum(1 for r in existing_results if r['is_fukusho'])
                        existing_venue_stats[course_key]['results'] = existing_results
                        existing_venue_stats[course_key]['fukusho_rate'] = round((fukusho_count / len(existing_results)) * 100, 1)
                        existing_venue_stats[course_key]['race_count'] = len(existing_results)
            
            self.existing_data[jockey_name]['venue_course_stats'] = existing_venue_stats
            self.update_count += 1
    
    def process_updates(self):
        """差分更新処理を実行"""
        jockeys = self.get_updated_jockeys()
        
        if not jockeys:
            logging.warning("更新対象の騎手が見つかりません")
            return False
        
        total = len(jockeys)
        logging.info(f"更新処理開始: {total}騎手")
        
        for i, jockey_name in enumerate(jockeys, 1):
            if i % 10 == 0:
                elapsed = time.time() - self.start_time
                rate = i / elapsed if elapsed > 0 else 0
                eta = (total - i) / rate if rate > 0 else 0
                logging.info(f"進捗: {i}/{total} ({i/total*100:.1f}%) - 残り時間: {eta/60:.1f}分")
            
            # 新規データ取得（8月17日以降）
            venue_data = self.get_jockey_venue_course_results(jockey_name, self.update_from_date)
            
            if venue_data:
                self.merge_jockey_data(jockey_name, venue_data)
        
        logging.info(f"更新完了: {self.update_count}騎手更新, {self.new_jockey_count}騎手追加")
        return True
    
    def save_updated_knowledge(self):
        """更新されたナレッジファイルを保存"""
        # バックアップ作成
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f'data/jockey_knowledge_backup_{timestamp}.json'
        
        if os.path.exists('data/jockey_knowledge.json'):
            shutil.copy2('data/jockey_knowledge.json', backup_path)
            logging.info(f"バックアップ作成: {backup_path}")
        
        # 更新ファイル保存
        output_path = 'data/jockey_knowledge.json'
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(self.existing_data, f, ensure_ascii=False, indent=2)
            
            # 圧縮版も作成
            with open(output_path, 'rb') as f_in:
                with gzip.open(f'{output_path}.gz', 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # ファイルサイズ確認
            size = os.path.getsize(output_path) / (1024 * 1024)  # MB
            compressed_size = os.path.getsize(f'{output_path}.gz') / (1024 * 1024)
            
            logging.info(f"保存完了: {output_path} ({size:.2f}MB)")
            logging.info(f"圧縮版: {output_path}.gz ({compressed_size:.2f}MB)")
            
            # 統計情報
            logging.info(f"総騎手数: {len(self.existing_data)}")
            
            return True
            
        except Exception as e:
            logging.error(f"ファイル保存エラー: {e}")
            return False
    
    def run(self):
        """メイン処理"""
        logging.info("=" * 50)
        logging.info("騎手ナレッジファイル差分更新開始")
        logging.info(f"更新対象期間: {self.update_from_date} 以降")
        logging.info("=" * 50)
        
        # データベース接続
        if not self.connect_to_database():
            return False
        
        # 既存データ読み込み
        if not self.load_existing_knowledge():
            logging.warning("既存データなし。新規作成モードで実行します。")
            self.existing_data = {}
        
        # 差分更新処理
        if not self.process_updates():
            return False
        
        # ファイル保存
        if not self.save_updated_knowledge():
            return False
        
        # 接続クローズ
        if self.connection:
            self.connection.close()
        
        # 処理時間
        total_time = time.time() - self.start_time
        logging.info(f"処理完了 - 総時間: {total_time/60:.1f}分")
        
        return True

if __name__ == "__main__":
    updater = JockeyKnowledgeUpdater()
    success = updater.run()
    
    if success:
        print("\n✅ 騎手ナレッジファイルの差分更新が完了しました")
        print("次のステップ:")
        print("1. data/jockey_knowledge.json を確認")
        print("2. CDNにアップロード: python upload_to_cdn.py")
    else:
        print("\n❌ 更新処理中にエラーが発生しました")
        print("ログファイルを確認してください: data/jockey_knowledge_update.log")