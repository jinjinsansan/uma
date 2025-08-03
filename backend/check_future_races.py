#!/usr/bin/env python3
"""
mykeibadb 未来レースデータ確認
"""  
import mysql.connector
import os
from datetime import date, timedelta
from dotenv import load_dotenv

# .envファイル読み込み
from pathlib import Path
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

def check_future_races():
    """未来のレースデータ確認"""
    mysql_config = {
        'host': os.getenv('MYSQL_HOST', 'localhost'),
        'port': int(os.getenv('MYSQL_PORT', 3306)),
        'user': os.getenv('MYSQL_USER', 'root'),
        'password': os.getenv('MYSQL_PASSWORD', ''),
        'database': os.getenv('MYSQL_DATABASE', 'mykeibadb'),
        'charset': 'utf8mb4'
    }
    
    try:
        conn = mysql.connector.connect(**mysql_config)
        cursor = conn.cursor()
        
        print("📅 mykeibadb レースデータ範囲調査")
        print("=" * 50)
        
        # テーブル構造確認
        cursor.execute("DESCRIBE umagoto_race_joho")
        columns = [col[0] for col in cursor.fetchall()]
        print(f"📊 テーブルカラム数: {len(columns)}")
        
        # 日付関連カラムを探す
        date_columns = [col for col in columns if 'DATE' in col.upper() or 'BI' in col.upper()]
        print(f"📅 日付関連カラム: {date_columns}")
        
        # 正しい日付カラムを特定
        date_col = 'KAISAI_BI'  # 一般的な競馬DBの開催日カラム
        if date_col not in columns:
            # 他の可能性を探す
            for col in date_columns:
                print(f"🔍 {col} カラムをテスト中...")
                try:
                    cursor.execute(f"SELECT MIN({col}), MAX({col}) FROM umagoto_race_joho LIMIT 1")
                    min_val, max_val = cursor.fetchone()
                    if min_val and max_val:
                        date_col = col
                        break
                except:
                    continue
        
        print(f"✅ 使用する日付カラム: {date_col}")
        
        # データ範囲確認
        cursor.execute(f"SELECT MIN({date_col}), MAX({date_col}) FROM umagoto_race_joho")
        min_date, max_date = cursor.fetchone()
        print(f"最古データ: {min_date}")
        print(f"最新データ: {max_date}")
        
        # 今日から1週間先のデータ確認
        print(f"\\n🔍 今日から1週間のレースデータ:")
        today = date.today()
        
        future_races_found = False
        for i in range(8):
            check_date = today + timedelta(days=i)
            date_str = check_date.strftime('%Y-%m-%d')
            
            cursor.execute(f"SELECT COUNT(*) FROM umagoto_race_joho WHERE {date_col} = %s", (date_str,))
            count = cursor.fetchone()[0]
            
            day_name = check_date.strftime('%a')
            status = '🏇 開催予定' if count > 0 else '❌ 開催なし'
            print(f"  {check_date} ({day_name}): {count}レース {status}")
            
            if count > 0:
                future_races_found = True
                # 競馬場情報取得
                cursor.execute(f"SELECT DISTINCT KEIBAJO_NAME FROM umagoto_race_joho WHERE {date_col} = %s", (date_str,))
                courses = cursor.fetchall()
                course_names = [c[0] for c in courses if c[0]]
                print(f"    📍 開催競馬場: {', '.join(course_names)}")
                
                # サンプルレース確認
                cursor.execute(f"SELECT RACE_BANGO, KYOSOMEI_HONDAI FROM umagoto_race_joho WHERE {date_col} = %s LIMIT 3", (date_str,))
                sample_races = cursor.fetchall()
                for race in sample_races:
                    print(f"    🏁 {race[0]}R {race[1] or '名称未定'}")
        
        if not future_races_found:
            print(f"\\n⚠️  結論: mykeibadbには未来のレースデータが含まれていません")
            print(f"   このデータベースは過去の結果データのみを保存している可能性があります")
            print(f"   リアルタイム予想には外部API（JRA-VAN等）との連携が必要です")
        else:
            print(f"\\n✅ 結論: 未来のレースデータが確認できました！")
            print(f"   競馬予想アプリとして使用可能です")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ エラー: {e}")

if __name__ == "__main__":
    check_future_races()