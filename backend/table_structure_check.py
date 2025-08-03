#!/usr/bin/env python3
"""
umagoto_race_johoテーブル構造確認
"""
import mysql.connector
import os
from dotenv import load_dotenv
from pathlib import Path

# .env読み込み
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

def check_table_structure():
    """テーブル構造確認"""
    config = {
        'host': '172.25.160.1',
        'port': 3306,
        'user': 'root',
        'password': '04050405Aoi-',
        'database': 'mykeibadb',
        'charset': 'utf8mb4'
    }
    
    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        
        print("🔍 umagoto_race_joho テーブル構造確認")
        print("=" * 50)
        
        # テーブル構造取得
        cursor.execute("DESCRIBE umagoto_race_joho")
        columns = cursor.fetchall()
        
        print(f"カラム数: {len(columns)}")
        print()
        print("カラム名                    | データ型")
        print("-" * 50)
        
        for col in columns:
            print(f"{col[0]:<25} | {col[1]}")
        
        print()
        print("🔍 サンプルデータ（3件）:")
        cursor.execute("SELECT * FROM umagoto_race_joho LIMIT 3")
        samples = cursor.fetchall()
        
        # カラム名取得
        column_names = [desc[0] for desc in cursor.description]
        
        for i, sample in enumerate(samples, 1):
            print(f"\n--- サンプル{i} ---")
            for j, value in enumerate(sample):
                if value is not None and str(value).strip():
                    print(f"{column_names[j]}: {value}")
        
        conn.close()
        print("\n✅ テーブル構造確認完了")
        
    except Exception as e:
        print(f"❌ エラー: {e}")

if __name__ == "__main__":
    check_table_structure()