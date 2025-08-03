#!/usr/bin/env python3
"""
Phase D: mykeibadb完全調査システム
データベースの実データを全調査し、最大活用可能範囲を確定
"""
import sqlite3
import os
from typing import Dict, List, Tuple, Any
from datetime import datetime
import json

class DatabaseAnalyzer:
    """mykeibadb完全調査・分析クラス"""
    
    def __init__(self, db_name='mykeibadb'):
        """
        データベース接続初期化
        Args:
            db_name: データベース名（通常は'mykeibadb'）
        """
        # プロジェクトルートから見たデータベースパス
        self.db_path = os.path.join(os.path.dirname(__file__), '..', '..', f'{db_name}')
        self.db_name = db_name
        
        # データベース存在確認
        if not os.path.exists(self.db_path):
            print(f"⚠️  データベースファイルが見つかりません: {self.db_path}")
            print(f"   現在のディレクトリから検索中...")
            self._find_database()
    
    def _find_database(self):
        """データベースファイルを検索"""
        possible_paths = [
            f'{self.db_name}',
            f'../{self.db_name}',
            f'../../{self.db_name}',
            f'../../../{self.db_name}',
            f'backend/{self.db_name}',
            f'../backend/{self.db_name}'
        ]
        
        for path in possible_paths:
            full_path = os.path.abspath(path)
            if os.path.exists(full_path):
                self.db_path = full_path
                print(f"✅ データベース発見: {self.db_path}")
                return
        
        print(f"❌ データベースファイル '{self.db_name}' が見つかりません")
        print("   利用可能な場合のパス例:")
        for path in possible_paths:
            print(f"     {os.path.abspath(path)}")
    
    def get_database_connection(self):
        """データベース接続取得"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # 辞書風アクセス可能
            return conn
        except Exception as e:
            print(f"❌ データベース接続エラー: {e}")
            return None
    
    def analyze_complete_database(self) -> Dict[str, Any]:
        """データベース完全調査"""
        print("🔍 mykeibadb完全調査開始...")
        
        conn = self.get_database_connection()
        if not conn:
            return {"error": "データベース接続失敗"}
        
        try:
            analysis_result = {
                "database_info": self._get_database_info(conn),
                "table_analysis": self._analyze_all_tables(conn),
                "horse_analysis": self._analyze_horses(conn),
                "race_analysis": self._analyze_races(conn),
                "date_analysis": self._analyze_date_range(conn),
                "grade_analysis": self._analyze_grades(conn),
                "performance_analysis": self._analyze_performance(conn),
                "data_quality": self._analyze_data_quality(conn)
            }
            
            return analysis_result
            
        except Exception as e:
            print(f"❌ 調査中エラー: {e}")
            return {"error": str(e)}
        finally:
            conn.close()
    
    def _get_database_info(self, conn) -> Dict[str, Any]:
        """データベース基本情報取得"""
        cursor = conn.cursor()
        
        # ファイルサイズ
        file_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
        
        # テーブル一覧
        tables = cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
        """).fetchall()
        
        return {
            "file_path": self.db_path,
            "file_size_mb": round(file_size / (1024 * 1024), 2),
            "table_count": len(tables),
            "table_names": [table[0] for table in tables]
        }
    
    def _analyze_all_tables(self, conn) -> Dict[str, Any]:
        """全テーブル分析"""
        cursor = conn.cursor()
        table_analysis = {}
        
        tables = cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
        """).fetchall()
        
        for table in tables:
            table_name = table[0]
            
            # レコード数
            count = cursor.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            
            # カラム情報
            columns = cursor.execute(f"PRAGMA table_info({table_name})").fetchall()
            
            table_analysis[table_name] = {
                "record_count": count,
                "column_count": len(columns),
                "columns": [(col[1], col[2]) for col in columns]  # (name, type)
            }
        
        return table_analysis
    
    def _analyze_horses(self, conn) -> Dict[str, Any]:
        """馬データ分析"""
        cursor = conn.cursor()
        
        # 総馬数（重複除去）
        total_horses = cursor.execute("""
            SELECT COUNT(DISTINCT BAMEI) 
            FROM umagoto_race_joho 
            WHERE BAMEI IS NOT NULL AND BAMEI != ''
        """).fetchone()[0]
        
        # 出走回数別分析
        race_count_analysis = cursor.execute("""
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
        """).fetchall()
        
        return {
            "total_horses": total_horses,
            "race_count_distribution": [(row[0], row[1]) for row in race_count_analysis[:20]]  # 上位20パターン
        }
    
    def _analyze_races(self, conn) -> Dict[str, Any]:
        """レースデータ分析"""
        cursor = conn.cursor()
        
        # 総レース数
        total_races = cursor.execute("SELECT COUNT(*) FROM umagoto_race_joho").fetchone()[0]
        
        # ユニークレース数
        unique_races = cursor.execute("""
            SELECT COUNT(DISTINCT RACE_CODE) FROM umagoto_race_joho
            WHERE RACE_CODE IS NOT NULL
        """).fetchone()[0]
        
        return {
            "total_race_records": total_races,
            "unique_races": unique_races,
            "average_horses_per_race": round(total_races / unique_races, 1) if unique_races > 0 else 0
        }
    
    def _analyze_date_range(self, conn) -> Dict[str, Any]:
        """日付範囲分析"""
        cursor = conn.cursor()
        
        date_range = cursor.execute("""
            SELECT MIN(KAISAI_DATE), MAX(KAISAI_DATE) 
            FROM umagoto_race_joho 
            WHERE KAISAI_DATE IS NOT NULL AND KAISAI_DATE != ''
        """).fetchone()
        
        return {
            "start_date": date_range[0] if date_range[0] else "不明",
            "end_date": date_range[1] if date_range[1] else "不明",
            "period_description": f"{date_range[0]} ～ {date_range[1]}" if date_range[0] and date_range[1] else "期間不明"
        }
    
    def _analyze_grades(self, conn) -> Dict[str, Any]:
        """グレード分析"""
        cursor = conn.cursor()
        
        try:
            # race_shosaiテーブルが存在するかチェック
            tables = cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='race_shosai'
            """).fetchall()
            
            if not tables:
                return {"note": "race_shosaiテーブルが存在しないため、グレード分析不可"}
            
            grade_analysis = cursor.execute("""
                SELECT 
                    CASE 
                        WHEN rs.GRADE_CODE LIKE '%G1%' THEN 'G1'
                        WHEN rs.GRADE_CODE LIKE '%G2%' THEN 'G2' 
                        WHEN rs.GRADE_CODE LIKE '%G3%' THEN 'G3'
                        ELSE 'その他'
                    END as grade,
                    COUNT(DISTINCT ur.BAMEI) as horse_count,
                    COUNT(*) as race_count
                FROM umagoto_race_joho ur
                LEFT JOIN race_shosai rs ON ur.RACE_CODE = rs.RACE_CODE
                GROUP BY grade
                ORDER BY race_count DESC
            """).fetchall()
            
            return {
                "grade_distribution": [(row[0], row[1], row[2]) for row in grade_analysis]
            }
            
        except Exception as e:
            return {"error": f"グレード分析エラー: {e}"}
    
    def _analyze_performance(self, conn) -> Dict[str, Any]:
        """成績分析"""
        cursor = conn.cursor()
        
        # 勝利数別分析
        win_analysis = cursor.execute("""
            SELECT 
                wins_count,
                COUNT(*) as horse_count
            FROM (
                SELECT BAMEI, 
                       SUM(CASE WHEN CHAKUJUN = 1 THEN 1 ELSE 0 END) as wins_count
                FROM umagoto_race_joho 
                WHERE CHAKUJUN IS NOT NULL
                GROUP BY BAMEI
            ) win_stats
            GROUP BY wins_count
            ORDER BY wins_count DESC
        """).fetchall()
        
        return {
            "win_distribution": [(row[0], row[1]) for row in win_analysis[:20]]  # 上位20パターン
        }
    
    def _analyze_data_quality(self, conn) -> Dict[str, Any]:
        """データ品質分析"""
        cursor = conn.cursor()
        
        # NULL値チェック
        total_records = cursor.execute("SELECT COUNT(*) FROM umagoto_race_joho").fetchone()[0]
        
        null_analysis = {}
        key_columns = ['BAMEI', 'RACE_CODE', 'KAISAI_DATE', 'CHAKUJUN']
        
        for column in key_columns:
            null_count = cursor.execute(f"""
                SELECT COUNT(*) FROM umagoto_race_joho 
                WHERE {column} IS NULL OR {column} = ''
            """).fetchone()[0]
            
            null_analysis[column] = {
                "null_count": null_count,
                "null_percentage": round(null_count / total_records * 100, 2) if total_records > 0 else 0
            }
        
        return null_analysis
    
    def get_optimal_horse_list(self, min_races=2, limit=None) -> List[Tuple]:
        """最適な馬リストを動的生成"""
        conn = self.get_database_connection()
        if not conn:
            return []
        
        try:
            query = """
            SELECT BAMEI, 
                   COUNT(*) as total_races,
                   SUM(CASE WHEN CHAKUJUN = 1 THEN 1 ELSE 0 END) as wins,
                   SUM(CASE WHEN CHAKUJUN <= 3 THEN 1 ELSE 0 END) as top3,
                   AVG(CAST(CHAKUJUN AS REAL)) as avg_finish,
                   COUNT(DISTINCT RACE_CODE) as unique_races
            FROM umagoto_race_joho 
            WHERE BAMEI IS NOT NULL AND BAMEI != ''
              AND CHAKUJUN IS NOT NULL AND CHAKUJUN != ''
            GROUP BY BAMEI 
            HAVING total_races >= ?
            ORDER BY 
                wins DESC,           -- 勝利数順
                total_races DESC,    -- 出走数順
                avg_finish ASC       -- 平均着順順
            """
            
            if limit:
                query += f" LIMIT {limit}"
            
            result = conn.execute(query, (min_races,)).fetchall()
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
            filename = f"mykeibadb_analysis_report_{timestamp}.json"
        
        filepath = os.path.join(os.path.dirname(__file__), '..', 'reports', filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # タイムスタンプ追加
        analysis_result["analysis_timestamp"] = datetime.now().isoformat()
        analysis_result["analyzer_version"] = "1.0.0"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(analysis_result, f, indent=2, ensure_ascii=False)
        
        print(f"📊 分析レポート出力: {filepath}")
        return filepath

if __name__ == "__main__":
    # スタンドアロン実行用テスト
    analyzer = DatabaseAnalyzer()
    
    print("🚀 mykeibadb完全調査テスト実行")
    analysis = analyzer.analyze_complete_database()
    
    if "error" in analysis:
        print(f"❌ エラー: {analysis['error']}")
    else:
        print("✅ 調査完了")
        print(f"📊 基本情報: {analysis.get('database_info', {})}")
        
        # レポート出力
        analyzer.export_analysis_report(analysis)