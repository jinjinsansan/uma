#!/usr/bin/env python3
"""
実際のmykeibadbデータテスト
"""
import mysql.connector
from datetime import date, timedelta

def test_real_race_data():
    """実際のレースデータテスト"""
    try:
        conn = mysql.connector.connect(
            host='172.25.160.1',
            port=3306,
            user='root',
            password='',
            database='mykeibadb',
            charset='utf8mb4'
        )
        
        cursor = conn.cursor(dictionary=True)
        
        # テーブル構造確認
        print("📊 レース関連テーブル確認:")
        cursor.execute("SHOW TABLES LIKE '%race%'")
        race_tables = cursor.fetchall()
        print("レース関連テーブル:")
        for table in race_tables:
            print(f"  - {list(table.values())[0]}")
        
        # umagoto_race_joho テーブル構造確認
        print("\n🏇 umagoto_race_joho テーブル構造:")
        cursor.execute("DESCRIBE umagoto_race_joho")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  {col['Field']} - {col['Type']}")
            
        # 最新データ確認（日付の範囲を広げて確認）
        print("\n📅 最新レースデータ:")
        cursor.execute("SELECT KAISAI_BI, KEIBAJO_CODE, RACE_BANGO, KYOSOMEI_HONDAI FROM umagoto_race_joho ORDER BY KAISAI_BI DESC LIMIT 5")
        recent_races = cursor.fetchall()
        for race in recent_races:
            print(f"  {race['KAISAI_BI']} {race['KEIBAJO_CODE']} {race['RACE_BANGO']}R {race.get('KYOSOMEI_HONDAI', '名称なし')}")
            
        # 今日の日付でのデータ確認
        today = date.today().strftime('%Y-%m-%d')
        print(f"\n📅 {today} のレースデータ:")
        cursor.execute("SELECT COUNT(*) as count FROM umagoto_race_joho WHERE KAISAI_BI = %s", (today,))
        today_count = cursor.fetchone()
        print(f"  本日のレース数: {today_count['count']}")
        
        if today_count['count'] == 0:
            # 直近1週間のデータを確認
            print("\n📅 直近1週間のレースデータ:")
            for i in range(7):
                check_date = (date.today() - timedelta(days=i)).strftime('%Y-%m-%d')
                cursor.execute("SELECT COUNT(*) as count FROM umagoto_race_joho WHERE KAISAI_BI = %s", (check_date,))
                day_count = cursor.fetchone()
                if day_count['count'] > 0:
                    print(f"  {check_date}: {day_count['count']}レース")
        
        cursor.close()
        conn.close()
        print("\n✅ 実データ確認完了")
        
    except Exception as e:
        print(f"❌ エラー: {e}")

if __name__ == "__main__":
    test_real_race_data()