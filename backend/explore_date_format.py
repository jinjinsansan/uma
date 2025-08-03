#!/usr/bin/env python3
"""
競馬データベースの日付形式確認
"""
import mysql.connector
import os
from datetime import date, timedelta
from dotenv import load_dotenv

# .envファイル読み込み
from pathlib import Path
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

def explore_date_format():
    """日付形式探索"""
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
        
        print("📅 競馬データの日付形式調査")
        print("=" * 50)
        
        # 日付関連カラムのサンプルを表示
        date_columns = ['KAISAI_NEN', 'KAISAI_GAPPI', 'DATA_SAKUSEI_NENGAPPI']
        
        for col in date_columns:
            print(f"\n🔍 {col} サンプルデータ:")
            cursor.execute(f"SELECT DISTINCT {col} FROM umagoto_race_joho WHERE {col} IS NOT NULL AND {col} != '' AND {col} != '0000' ORDER BY {col} DESC LIMIT 10")
            samples = cursor.fetchall()
            for sample in samples:
                print(f"  {sample[0]}")
        
        # 最新のレースデータを確認
        print(f"\n🏇 最新レースデータ:")
        cursor.execute("""
            SELECT KAISAI_NEN, KAISAI_GAPPI, KEIBAJO_CODE, RACE_BANGO, BAMEI 
            FROM umagoto_race_joho 
            WHERE KAISAI_NEN IS NOT NULL AND KAISAI_NEN != '' AND KAISAI_NEN != '0000'
            ORDER BY KAISAI_NEN DESC, KAISAI_GAPPI DESC 
            LIMIT 10
        """)
        recent = cursor.fetchall()
        for race in recent:
            kaisai_nen = race[0]
            kaisai_gappi = race[1]
            keibajo = race[2]
            bango = race[3]
            bamei = race[4]
            
            # 日付を解析してみる
            try:
                if len(kaisai_gappi) == 4:
                    month = kaisai_gappi[:2]
                    day = kaisai_gappi[2:]
                    formatted_date = f"{kaisai_nen}-{month}-{day}"
                else:
                    formatted_date = f"{kaisai_nen}-{kaisai_gappi}"
            except:
                formatted_date = f"{kaisai_nen}-{kaisai_gappi}"
            
            print(f"  {formatted_date} {keibajo} {bango}R {bamei}")
        
        # 今日の日付での検索を試行
        today = date.today()
        today_year = today.strftime('%Y')
        today_gappi = today.strftime('%m%d')
        
        print(f"\n📊 本日({today})のレースデータ検索:")
        print(f"  年: {today_year}, 月日: {today_gappi}")
        
        cursor.execute("""
            SELECT COUNT(*) FROM umagoto_race_joho 
            WHERE KAISAI_NEN = %s AND KAISAI_GAPPI = %s
        """, (today_year, today_gappi))
        today_count = cursor.fetchone()[0]
        print(f"  本日のレース数: {today_count}")
        
        # 明日の検索
        tomorrow = today + timedelta(days=1)
        tomorrow_year = tomorrow.strftime('%Y')
        tomorrow_gappi = tomorrow.strftime('%m%d')
        
        print(f"\n📊 明日({tomorrow})のレースデータ検索:")
        print(f"  年: {tomorrow_year}, 月日: {tomorrow_gappi}")
        
        cursor.execute("""
            SELECT COUNT(*) FROM umagoto_race_joho 
            WHERE KAISAI_NEN = %s AND KAISAI_GAPPI = %s
        """, (tomorrow_year, tomorrow_gappi))
        tomorrow_count = cursor.fetchone()[0]
        print(f"  明日のレース数: {tomorrow_count}")
        
        # 結論
        print(f"\n📝 結論:")
        if today_count > 0 or tomorrow_count > 0:
            print("✅ 当日または翌日のレースデータが見つかりました")
            print("   競馬予想アプリとして使用可能です")
        else:
            print("⚠️  当日・翌日のレースデータが見つかりません")
            print("   過去のレース結果データのみの可能性があります")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ エラー: {e}")

if __name__ == "__main__":
    explore_date_format()