#!/usr/bin/env python3
"""
mykeibadb 日付範囲と未来データ簡易確認
"""
import mysql.connector
import os
from datetime import date, timedelta
from dotenv import load_dotenv

# .envファイル読み込み
from pathlib import Path
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

def quick_check():
    """簡易データ確認"""
    try:
        # 基本接続設定（mysql_test.pyと同じ）
        mysql_config = {
            'host': os.getenv('MYSQL_HOST', 'localhost'),
            'port': int(os.getenv('MYSQL_PORT', 3306)),
            'user': os.getenv('MYSQL_USER', 'root'),
            'password': os.getenv('MYSQL_PASSWORD', ''),
            'database': os.getenv('MYSQL_DATABASE', 'mykeibadb'),
            'charset': 'utf8mb4'
        }
        
        print(f"接続先: {mysql_config['host']}:{mysql_config['port']}")
        conn = mysql.connector.connect(**mysql_config)
        cursor = conn.cursor()
        
        print("📅 mykeibadb レースデータ範囲調査")
        print("=" * 50)
        
        # データ範囲確認
        cursor.execute("SELECT MIN(KAISAI_BI), MAX(KAISAI_BI) FROM umagoto_race_joho")
        min_date, max_date = cursor.fetchone()
        print(f"最古データ: {min_date}")
        print(f"最新データ: {max_date}")
        
        # 今日から1週間の確認
        today = date.today()
        print(f"\n🔍 今日から1週間のレースデータ:")
        
        future_races_found = False
        for i in range(8):  # 今日から7日後まで
            check_date = today + timedelta(days=i)
            date_str = check_date.strftime('%Y-%m-%d')
            
            cursor.execute("SELECT COUNT(*) FROM umagoto_race_joho WHERE KAISAI_BI = %s", (date_str,))
            count = cursor.fetchone()[0]
            
            day_name = check_date.strftime('%a')
            status = '🏇 開催予定' if count > 0 else '❌ 開催なし'
            print(f"  {check_date} ({day_name}): {count}レース {status}")
            
            if count > 0:
                future_races_found = True
        
        # 結論
        print(f"\n📊 結論:")
        if future_races_found:
            print("✅ 未来のレースデータが確認できました！")
            print("   競馬予想アプリとして使用可能です")
        else:
            print("⚠️  mykeibadbには未来のレースデータが含まれていません")
            print("   このデータベースは過去の結果データのみを保存している可能性があります")
            print("   リアルタイム予想には外部API（JRA-VAN等）との連携が必要です")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ エラー: {e}")

if __name__ == "__main__":
    quick_check()