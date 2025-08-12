#!/usr/bin/env python3
"""
月次ナレッジファイル更新サービス
MySQLから差分データを取得して新しいナレッジファイルを生成
"""
import json
import os
import mysql.connector
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
import gzip
import shutil

logger = logging.getLogger(__name__)

class MonthlyKnowledgeUpdater:
    """月次ナレッジファイル更新サービス"""
    
    def __init__(self):
        self.mysql_config = {
            'host': '172.25.160.1',
            'port': 3306,
            'user': 'root',
            'password': '04050405Aoi-',
            'database': 'mykeibadb',
            'charset': 'utf8mb4'
        }
        self.output_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'monthly_updates')
        os.makedirs(self.output_dir, exist_ok=True)
        
    def get_last_update_date(self) -> datetime:
        """最後の更新日を取得（メタデータから）"""
        try:
            # 現在のナレッジファイルのメタデータを確認
            from .dlogic_raw_data_manager import dlogic_manager
            meta_info = dlogic_manager.knowledge_data.get('meta', {})
            last_updated = meta_info.get('last_updated', '2024-12-01')
            return datetime.strptime(last_updated, '%Y-%m-%d')
        except Exception as e:
            logger.warning(f"Failed to get last update date: {e}")
            # デフォルトは1ヶ月前
            return datetime.now() - timedelta(days=30)
    
    def fetch_new_horses(self, since_date: datetime) -> List[str]:
        """指定日以降に3走以上した馬名リストを取得"""
        conn = None
        cursor = None
        try:
            conn = mysql.connector.connect(**self.mysql_config)
            cursor = conn.cursor()
            
            # 指定日以降に3走以上した馬を検索
            query = """
            SELECT DISTINCT BAMEI
            FROM jvd_ks
            WHERE NENGAPPI >= %s
              AND BAMEI IS NOT NULL
              AND BAMEI != ''
            GROUP BY BAMEI
            HAVING COUNT(*) >= 3
            ORDER BY BAMEI
            """
            
            cursor.execute(query, (since_date.strftime('%Y%m%d'),))
            horses = [row[0] for row in cursor.fetchall()]
            
            logger.info(f"Found {len(horses)} horses with 3+ races since {since_date}")
            return horses
            
        except Exception as e:
            logger.error(f"Error fetching new horses: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def get_horse_race_data(self, horse_name: str) -> List[Dict[str, Any]]:
        """馬の過去走データを取得"""
        conn = None
        cursor = None
        try:
            conn = mysql.connector.connect(**self.mysql_config)
            cursor = conn.cursor(dictionary=True)
            
            query = """
            SELECT 
                NENGAPPI,
                KYOSOMEI_HONDAI,
                TRACK_CODE,
                KYORI,
                BABA_CODE,
                TENKO_CODE,
                KISHUMEI_RYAKUSHO,
                CHOKYOSHIMEI_RYAKUSHO,
                KAKUTEI_JINI,
                KAKUTEI_CHAKUSA,
                TANSHO_NINKIJUN,
                FUTAN_JURYO,
                BATAIJU,
                ZOGEN_FUGO,
                ZOGEN_SA,
                CORNER1_JUNI,
                CORNER2_JUNI,
                CORNER3_JUNI,
                CORNER4_JUNI,
                SOHA_TIME,
                JOKYO_CODE,
                GRADE_CODE,
                SYUSSO_TOSU
            FROM jvd_ks
            WHERE BAMEI = %s
            ORDER BY NENGAPPI DESC
            LIMIT 10
            """
            
            cursor.execute(query, (horse_name,))
            races = cursor.fetchall()
            
            return races
            
        except Exception as e:
            logger.error(f"Error fetching race data for {horse_name}: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def merge_with_existing_knowledge(self, new_data: Dict[str, Any]) -> Dict[str, Any]:
        """既存のナレッジデータと新データをマージ"""
        try:
            from .dlogic_raw_data_manager import dlogic_manager
            existing_data = dlogic_manager.knowledge_data.copy()
            
            # 既存の馬データに新データを追加/更新
            existing_horses = existing_data.get('horses', {})
            new_horses = new_data.get('horses', {})
            
            # マージ（新データで上書き）
            for horse_name, horse_data in new_horses.items():
                existing_horses[horse_name] = horse_data
            
            # メタデータ更新
            existing_data['meta'] = {
                'total_horses': len(existing_horses),
                'last_updated': datetime.now().strftime('%Y-%m-%d'),
                'update_type': 'monthly_differential',
                'previous_update': existing_data.get('meta', {}).get('last_updated', 'unknown'),
                'new_horses_added': len(new_horses),
                'generation_date': datetime.now().isoformat()
            }
            
            existing_data['horses'] = existing_horses
            return existing_data
            
        except Exception as e:
            logger.error(f"Error merging knowledge data: {e}")
            # エラー時は新データのみ返す
            return new_data
    
    def generate_monthly_update(self) -> Dict[str, Any]:
        """月次更新データを生成"""
        logger.info("Starting monthly knowledge update generation")
        
        # 最後の更新日を取得
        last_update = self.get_last_update_date()
        logger.info(f"Last update date: {last_update}")
        
        # 新しい馬のリストを取得
        new_horses = self.fetch_new_horses(last_update)
        logger.info(f"Found {len(new_horses)} new/updated horses")
        
        # 新しい馬のデータを収集
        knowledge_data = {
            'horses': {},
            'meta': {
                'generation_date': datetime.now().isoformat(),
                'last_updated': datetime.now().strftime('%Y-%m-%d'),
                'update_type': 'monthly_differential',
                'previous_update': last_update.strftime('%Y-%m-%d'),
                'new_horses_count': len(new_horses)
            }
        }
        
        for i, horse_name in enumerate(new_horses):
            if i % 100 == 0:
                logger.info(f"Processing horse {i+1}/{len(new_horses)}")
            
            race_data = self.get_horse_race_data(horse_name)
            if race_data:
                knowledge_data['horses'][horse_name] = {
                    'race_count': len(race_data),
                    'races': race_data,
                    'last_race_date': race_data[0]['NENGAPPI'] if race_data else None
                }
        
        # 既存データとマージ
        merged_data = self.merge_with_existing_knowledge(knowledge_data)
        
        # ファイルに保存
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_filename = f"dlogic_knowledge_update_{timestamp}.json"
        output_path = os.path.join(self.output_dir, output_filename)
        
        # JSON形式で保存
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(merged_data, f, ensure_ascii=False, indent=2)
        
        # 圧縮版も作成
        gz_path = output_path + '.gz'
        with open(output_path, 'rb') as f_in:
            with gzip.open(gz_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        logger.info(f"Monthly update generated: {output_path}")
        
        return {
            'status': 'success',
            'file_path': output_path,
            'gz_file_path': gz_path,
            'file_size_mb': os.path.getsize(output_path) / (1024 * 1024),
            'gz_file_size_mb': os.path.getsize(gz_path) / (1024 * 1024),
            'total_horses': len(merged_data.get('horses', {})),
            'new_horses': len(new_horses),
            'update_info': merged_data.get('meta', {})
        }
    
    def get_update_history(self) -> List[Dict[str, Any]]:
        """過去の更新履歴を取得"""
        history = []
        
        if not os.path.exists(self.output_dir):
            return history
        
        for filename in os.listdir(self.output_dir):
            if filename.endswith('.json') and filename.startswith('dlogic_knowledge_update_'):
                file_path = os.path.join(self.output_dir, filename)
                file_stat = os.stat(file_path)
                
                # ファイル名から日時を抽出
                try:
                    timestamp_str = filename.replace('dlogic_knowledge_update_', '').replace('.json', '')
                    update_time = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
                except:
                    update_time = datetime.fromtimestamp(file_stat.st_mtime)
                
                history.append({
                    'filename': filename,
                    'file_path': file_path,
                    'size_mb': file_stat.st_size / (1024 * 1024),
                    'created_at': update_time.isoformat(),
                    'has_gz': os.path.exists(file_path + '.gz')
                })
        
        # 新しい順にソート
        history.sort(key=lambda x: x['created_at'], reverse=True)
        return history[:10]  # 最新10件のみ

if __name__ == "__main__":
    # テスト実行
    updater = MonthlyKnowledgeUpdater()
    result = updater.generate_monthly_update()
    print(json.dumps(result, indent=2, ensure_ascii=False))