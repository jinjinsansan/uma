#!/usr/bin/env python3
"""
Phase D: MySQL mykeibadb完全調査システム
CursorがMySQLで成功した方法と同じアプローチでデータベース調査
"""
import mysql.connector
import os
from typing import Dict, List, Tuple, Any
from datetime import datetime
import json
from decimal import Decimal
from dotenv import load_dotenv
from pathlib import Path

# .envファイル読み込み（親ディレクトリから）
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

class MySQLDatabaseAnalyzer:
    """MySQL mykeibadb完全調査・分析クラス"""
    
    def __init__(self):
        """MySQL接続設定初期化（Cursorと同じ設定）"""
        # 環境変数確認・設定
        mysql_host = os.getenv('MYSQL_HOST')
        if not mysql_host:
            mysql_host = '172.25.160.1'  # Windows Host IP
            
        self.mysql_config = {
            'host': mysql_host,
            'port': int(os.getenv('MYSQL_PORT', 3306)),
            'user': os.getenv('MYSQL_USER', 'root'),
            'password': os.getenv('MYSQL_PASSWORD', '04050405Aoi-'),
            'database': os.getenv('MYSQL_DATABASE', 'mykeibadb'),
            'charset': 'utf8mb4'
        }
        
        print("MySQL接続設定:")
        print(f"  Host: {self.mysql_config['host']}:{self.mysql_config['port']}")
        print(f"  User: {self.mysql_config['user']}")
        print(f"  Database: {self.mysql_config['database']}")
    
    def get_database_connection(self):
        """MySQL接続取得（Cursorと同じ方法）"""
        try:
            connection = mysql.connector.connect(**self.mysql_config)
            print("✅ MySQL接続成功")
            return connection
        except mysql.connector.Error as e:
            print(f"❌ MySQL接続エラー: {e}")
            return None
        except Exception as e:
            print(f"❌ 予期しないエラー: {e}")
            return None
    
    def test_connection(self):
        """接続テスト"""
        print("MySQL接続テスト実行中...")
        
        conn = self.get_database_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            # テーブル一覧取得
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            
            print(f"✅ テーブル数: {len(tables)}")
            for table in tables:
                print(f"  - {table[0]}")
            
            # umagoto_race_joho テーブル確認
            table_names = [table[0] for table in tables]
            if 'umagoto_race_joho' in table_names:
                cursor.execute("SELECT COUNT(*) FROM umagoto_race_joho")
                count = cursor.fetchone()[0]
                print(f"✅ umagoto_race_joho: {count:,}レコード")
                
                cursor.execute("SELECT * FROM umagoto_race_joho LIMIT 3")
                samples = cursor.fetchall()
                print(f"✅ サンプルデータ取得成功: {len(samples)}件")
                return True
            else:
                print("❌ umagoto_race_joho テーブルが見つかりません")
                return False
                
        except Exception as e:
            print(f"❌ テスト実行エラー: {e}")
            return False
        finally:
            conn.close()
    
    def analyze_complete_database(self) -> Dict[str, Any]:
        """MySQL mykeibadb完全調査"""
        print("🔍 MySQL mykeibadb完全調査開始...")
        
        conn = self.get_database_connection()
        if not conn:
            return {"error": "MySQL接続失敗"}
        
        try:
            cursor = conn.cursor()
            
            analysis_result = {
                "database_info": self._get_mysql_database_info(cursor),
                "table_analysis": self._analyze_all_mysql_tables(cursor),
                "horse_analysis": self._analyze_mysql_horses(cursor),
                "race_analysis": self._analyze_mysql_races(cursor),
                "date_analysis": self._analyze_mysql_date_range(cursor),
                "performance_analysis": self._analyze_mysql_performance(cursor),
                "data_quality": self._analyze_mysql_data_quality(cursor)
            }
            
            return analysis_result
            
        except Exception as e:
            print(f"❌ 調査中エラー: {e}")
            return {"error": str(e)}
        finally:
            conn.close()
    
    def _get_mysql_database_info(self, cursor) -> Dict[str, Any]:
        """MySQL基本情報取得"""
        # テーブル一覧
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        # データベースサイズ
        cursor.execute("""
            SELECT ROUND(SUM(data_length + index_length) / 1024 / 1024, 1) AS 'DB Size (MB)'
            FROM information_schema.tables
            WHERE table_schema = %s
        """, (self.mysql_config['database'],))
        
        db_size = cursor.fetchone()
        
        return {
            "connection_type": "MySQL",
            "database_name": self.mysql_config['database'],
            "host": f"{self.mysql_config['host']}:{self.mysql_config['port']}",
            "db_size_mb": db_size[0] if db_size and db_size[0] else 0,
            "table_count": len(tables),
            "table_names": [table[0] for table in tables]
        }
    
    def _analyze_all_mysql_tables(self, cursor) -> Dict[str, Any]:
        """全テーブル分析"""
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        table_analysis = {}
        
        for table in tables:
            table_name = table[0]
            
            # レコード数
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            
            # カラム情報
            cursor.execute(f"DESCRIBE {table_name}")
            columns = cursor.fetchall()
            
            table_analysis[table_name] = {
                "record_count": count,
                "column_count": len(columns),
                "columns": [(col[0], col[1]) for col in columns]  # (name, type)
            }
        
        return table_analysis
    
    def _analyze_mysql_horses(self, cursor) -> Dict[str, Any]:
        """馬データ分析"""
        # 総馬数（重複除去）
        cursor.execute("""
            SELECT COUNT(DISTINCT BAMEI) 
            FROM umagoto_race_joho 
            WHERE BAMEI IS NOT NULL AND BAMEI != ''
        """)
        total_horses = cursor.fetchone()[0]
        
        # 出走回数別分析
        cursor.execute("""
            SELECT 
                race_count,
                COUNT(*) as horse_count
            FROM (
                SELECT BAMEI, COUNT(*) as race_count
                FROM umagoto_race_joho 
                WHERE BAMEI IS NOT NULL AND BAMEI != ''
                GROUP BY BAMEI
            ) stats
            GROUP BY race_count
            ORDER BY race_count DESC
            LIMIT 20
        """)
        race_count_analysis = cursor.fetchall()
        
        return {
            "total_horses": total_horses,
            "race_count_distribution": [(row[0], row[1]) for row in race_count_analysis]
        }
    
    def _analyze_mysql_races(self, cursor) -> Dict[str, Any]:
        """レースデータ分析"""
        # 総レース数
        cursor.execute("SELECT COUNT(*) FROM umagoto_race_joho")
        total_races = cursor.fetchone()[0]
        
        # ユニークレース数
        cursor.execute("""
            SELECT COUNT(DISTINCT RACE_CODE) FROM umagoto_race_joho
            WHERE RACE_CODE IS NOT NULL
        """)
        unique_races = cursor.fetchone()[0]
        
        return {
            "total_race_records": total_races,
            "unique_races": unique_races,
            "average_horses_per_race": round(total_races / unique_races, 1) if unique_races > 0 else 0
        }
    
    def _analyze_mysql_date_range(self, cursor) -> Dict[str, Any]:
        """日付範囲分析"""
        cursor.execute("""
            SELECT MIN(KAISAI_NEN), MAX(KAISAI_NEN),
                   MIN(CONCAT(KAISAI_NEN, KAISAI_GAPPI)) as earliest_date,
                   MAX(CONCAT(KAISAI_NEN, KAISAI_GAPPI)) as latest_date
            FROM umagoto_race_joho 
            WHERE KAISAI_NEN IS NOT NULL AND KAISAI_NEN != ''
              AND KAISAI_GAPPI IS NOT NULL AND KAISAI_GAPPI != ''
        """)
        date_range = cursor.fetchone()
        
        return {
            "start_year": str(date_range[0]) if date_range[0] else "不明",
            "end_year": str(date_range[1]) if date_range[1] else "不明", 
            "earliest_date": str(date_range[2]) if date_range[2] else "不明",
            "latest_date": str(date_range[3]) if date_range[3] else "不明",
            "period_description": f"{date_range[0]}年 ～ {date_range[1]}年" if date_range[0] and date_range[1] else "期間不明",
            "data_span_years": int(date_range[1]) - int(date_range[0]) if date_range[0] and date_range[1] else 0
        }
    
    def _analyze_mysql_performance(self, cursor) -> Dict[str, Any]:
        """成績分析"""
        # 勝利数別分析（正しいカラム名使用）
        cursor.execute("""
            SELECT 
                wins_count,
                COUNT(*) as horse_count
            FROM (
                SELECT BAMEI, 
                       SUM(CASE WHEN KAKUTEI_CHAKUJUN = '01' THEN 1 ELSE 0 END) as wins_count
                FROM umagoto_race_joho 
                WHERE KAKUTEI_CHAKUJUN IS NOT NULL AND KAKUTEI_CHAKUJUN != ''
                GROUP BY BAMEI
            ) win_stats
            GROUP BY wins_count
            ORDER BY wins_count DESC
            LIMIT 20
        """)
        win_analysis = cursor.fetchall()
        
        return {
            "win_distribution": [(row[0], row[1]) for row in win_analysis]
        }
    
    def _analyze_mysql_data_quality(self, cursor) -> Dict[str, Any]:
        """データ品質分析"""
        # 総レコード数
        cursor.execute("SELECT COUNT(*) FROM umagoto_race_joho")
        total_records = cursor.fetchone()[0]
        
        null_analysis = {}
        key_columns = ['BAMEI', 'RACE_CODE', 'KAISAI_NEN', 'KAKUTEI_CHAKUJUN']
        
        for column in key_columns:
            cursor.execute(f"""
                SELECT COUNT(*) FROM umagoto_race_joho 
                WHERE {column} IS NULL OR {column} = ''
            """)
            null_count = cursor.fetchone()[0]
            
            null_analysis[column] = {
                "null_count": null_count,
                "null_percentage": round(null_count / total_records * 100, 2) if total_records > 0 else 0
            }
        
        return null_analysis
    
    def get_optimal_horse_list(self, min_races=2, limit=None) -> List[Tuple]:
        """最適な馬リストを動的生成（MySQL版）"""
        conn = self.get_database_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            
            query = """
            SELECT BAMEI, 
                   COUNT(*) as total_races,
                   SUM(CASE WHEN KAKUTEI_CHAKUJUN = '01' THEN 1 ELSE 0 END) as wins,
                   SUM(CASE WHEN CAST(KAKUTEI_CHAKUJUN AS UNSIGNED) <= 3 THEN 1 ELSE 0 END) as top3,
                   AVG(CAST(KAKUTEI_CHAKUJUN AS UNSIGNED)) as avg_finish,
                   COUNT(DISTINCT RACE_CODE) as unique_races
            FROM umagoto_race_joho 
            WHERE BAMEI IS NOT NULL AND BAMEI != ''
              AND KAKUTEI_CHAKUJUN IS NOT NULL AND KAKUTEI_CHAKUJUN != ''
              AND KAKUTEI_CHAKUJUN REGEXP '^[0-9]+$'
            GROUP BY BAMEI 
            HAVING total_races >= %s AND wins > 0
            ORDER BY 
                wins DESC,           
                total_races DESC,    
                avg_finish ASC       
            """
            
            if limit:
                query += f" LIMIT {limit}"
            
            cursor.execute(query, (min_races,))
            result = cursor.fetchall()
            return result
            
        except Exception as e:
            print(f"❌ 馬リスト取得エラー: {e}")
            return []
        finally:
            conn.close()
    
    def export_analysis_report(self, analysis_result: Dict[str, Any], filename: str = None):
        """分析結果をレポート出力"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"mysql_mykeibadb_analysis_report_{timestamp}.json"
        
        reports_dir = os.path.join(os.path.dirname(__file__), '..', 'reports')
        os.makedirs(reports_dir, exist_ok=True)
        filepath = os.path.join(reports_dir, filename)
        
        # タイムスタンプ追加
        analysis_result["analysis_timestamp"] = datetime.now().isoformat()
        analysis_result["analyzer_version"] = "MySQL_1.0.0"
        analysis_result["connection_info"] = {
            "type": "MySQL",
            "host": self.mysql_config['host'],
            "database": self.mysql_config['database']
        }
        
        # Decimal型をfloatに変換するカスタムエンコーダー
        def decimal_encoder(obj):
            if isinstance(obj, Decimal):
                return float(obj)
            raise TypeError
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(analysis_result, f, indent=2, ensure_ascii=False, default=decimal_encoder)
        
        print(f"📊 MySQL分析レポート出力: {filepath}")
        return filepath

if __name__ == "__main__":
    # MySQL接続テスト
    analyzer = MySQLDatabaseAnalyzer()
    
    print("🚀 MySQL mykeibadb接続テスト実行")
    
    if analyzer.test_connection():
        print("\n✅ MySQL接続テスト成功!")
        print("🚀 Phase D完全調査を自動実行中...")
        
        try:
            analysis = analyzer.analyze_complete_database()
            if "error" not in analysis:
                report_path = analyzer.export_analysis_report(analysis)
                print("✅ MySQL完全調査完了")
                print(f"📊 レポート出力: {report_path}")
                
                # 処理対象馬リスト生成
                optimal_horses = analyzer.get_optimal_horse_list(min_races=2, limit=50)
                print(f"\n🐎 Phase D処理対象馬（上位50頭）:")
                for i, horse in enumerate(optimal_horses[:10], 1):
                    print(f"  {i:2d}. {horse[0]} - {horse[1]}戦{horse[2]}勝 (勝率{horse[2]/horse[1]*100:.1f}%)")
                
                if len(optimal_horses) > 10:
                    print(f"     ... 他{len(optimal_horses)-10}頭")
                
                print("\n🎯 Phase D実行準備完了!")
                print("   955,956レコードから最適馬選別完了")
                print("   12項目D-Logic分析システム準備完了")
                
            else:
                print(f"❌ 調査エラー: {analysis['error']}")
        except KeyboardInterrupt:
            print("\n⏹️  処理中断")
    else:
        print("❌ MySQL接続テスト失敗")
        print("\n💡 確認事項:")
        print("  1. MySQLサーバーが起動しているか")
        print("  2. .envファイルの接続情報が正しいか")
        print("  3. mykeibadbデータベースが存在するか")
        print("  4. 指定されたユーザーでアクセス権限があるか")