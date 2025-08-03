#!/usr/bin/env python3
"""
umagoto_race_joho テーブル構造確認
"""
import mysql.connector
import os
from dotenv import load_dotenv

# .envファイル読み込み
from pathlib import Path
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

def check_table_structure():
    """テーブル構造確認"""
    try:
        mysql_config = {
            'host': os.getenv('MYSQL_HOST', 'localhost'),
            'port': int(os.getenv('MYSQL_PORT', 3306)),
            'user': os.getenv('MYSQL_USER', 'root'),
            'password': os.getenv('MYSQL_PASSWORD', ''),
            'database': os.getenv('MYSQL_DATABASE', 'mykeibadb'),
            'charset': 'utf8mb4'
        }
        
        conn = mysql.connector.connect(**mysql_config)
        cursor = conn.cursor()
        
        print("📊 umagoto_race_joho テーブル構造:")
        cursor.execute("DESCRIBE umagoto_race_joho")
        columns = cursor.fetchall()
        
        date_columns = []
        for col in columns:
            field_name = col[0]
            field_type = col[1]
            print(f"  {field_name} - {field_type}")
            
            # 日付関連カラムを探す
            if 'DATE' in field_name.upper() or 'BI' in field_name.upper():
                date_columns.append(field_name)
        
        print(f"\n📅 日付関連カラム: {date_columns}")
        
        # サンプルデータで日付カラムを確認
        for date_col in date_columns:
            print(f"\n🔍 {date_col} サンプルデータ:")
            cursor.execute(f"SELECT {date_col} FROM umagoto_race_joho WHERE {date_col} IS NOT NULL LIMIT 5")
            samples = cursor.fetchall()
            for sample in samples:
                print(f"  {sample[0]}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ エラー: {e}")

if __name__ == "__main__":
    check_table_structure()