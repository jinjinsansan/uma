#!/usr/bin/env python3
"""
MySQL mykeibadb接続テスト（Windows対応）
"""
import mysql.connector
import os
from dotenv import load_dotenv

# .envファイル読み込み（親ディレクトリから）
import sys
sys.path.append('..')
from pathlib import Path
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

def test_mysql_connection():
    """MySQL接続テスト"""
    print("MySQL mykeibadb接続テスト")
    print("=" * 40)
    
    # 接続設定
    mysql_config = {
        'host': os.getenv('MYSQL_HOST', 'localhost'),
        'port': int(os.getenv('MYSQL_PORT', 3306)),
        'user': os.getenv('MYSQL_USER', 'root'),
        'password': os.getenv('MYSQL_PASSWORD', ''),
        'database': os.getenv('MYSQL_DATABASE', 'mykeibadb'),
        'charset': 'utf8mb4'
    }
    
    print(f"接続先: {mysql_config['host']}:{mysql_config['port']}")
    print(f"ユーザー: {mysql_config['user']}")
    print(f"データベース: {mysql_config['database']}")
    print()
    
    # 接続テスト
    try:
        print("MySQL接続試行中...")
        connection = mysql.connector.connect(**mysql_config)
        cursor = connection.cursor()
        
        print("SUCCESS: MySQL接続成功!")
        
        # テーブル一覧
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        print(f"テーブル数: {len(tables)}")
        table_names = [table[0] for table in tables]
        
        for table_name in table_names:
            print(f"  - {table_name}")
        
        # umagoto_race_joho テーブル確認
        if 'umagoto_race_joho' in table_names:
            cursor.execute("SELECT COUNT(*) FROM umagoto_race_joho")
            total_records = cursor.fetchone()[0]
            print(f"\numagoto_race_joho: {total_records:,}レコード")
            
            # 馬数確認
            cursor.execute("""
                SELECT COUNT(DISTINCT BAMEI) FROM umagoto_race_joho 
                WHERE BAMEI IS NOT NULL AND BAMEI != ''
            """)
            total_horses = cursor.fetchone()[0]
            print(f"総馬数: {total_horses:,}頭")
            
            # サンプルデータ
            cursor.execute("SELECT BAMEI, RACE_CODE, KAISAI_DATE, CHAKUJUN FROM umagoto_race_joho LIMIT 5")
            samples = cursor.fetchall()
            
            print("\nサンプルデータ:")
            for sample in samples:
                print(f"  {sample[0]} | {sample[1]} | {sample[2]} | {sample[3]}着")
            
            # 処理対象馬（2戦以上勝利馬）
            cursor.execute("""
                SELECT BAMEI, 
                       COUNT(*) as total_races,
                       SUM(CASE WHEN CHAKUJUN = 1 THEN 1 ELSE 0 END) as wins
                FROM umagoto_race_joho 
                WHERE BAMEI IS NOT NULL AND BAMEI != ''
                  AND CHAKUJUN IS NOT NULL AND CHAKUJUN != ''
                GROUP BY BAMEI 
                HAVING total_races >= 2 AND wins > 0
                ORDER BY wins DESC, total_races DESC
                LIMIT 10
            """)
            target_horses = cursor.fetchall()
            
            print(f"\nPhase D処理対象候補（2戦以上勝利馬）: {len(target_horses)}頭サンプル")
            for horse in target_horses:
                print(f"  {horse[0]}: {horse[1]}戦{horse[2]}勝")
            
            print("\n=== MySQL接続テスト成功 ===")
            print("Phase D実行準備完了!")
            print("MySQL版フルシステムでナレッジベース構築可能")
            
        else:
            print("ERROR: umagoto_race_johoテーブルが見つかりません")
            return False
        
        connection.close()
        return True
        
    except mysql.connector.Error as e:
        print(f"ERROR: MySQL接続エラー - {e}")
        print("\n確認事項:")
        print("  1. MySQLサーバーが起動しているか")
        print("  2. .envファイルの接続情報が正しいか")
        print("  3. mykeibadbデータベースが存在するか")
        print("  4. 指定されたユーザーでアクセス権限があるか")
        return False
    except Exception as e:
        print(f"ERROR: 予期しないエラー - {e}")
        return False

if __name__ == "__main__":
    success = test_mysql_connection()
    exit_code = 0 if success else 1
    exit(exit_code)