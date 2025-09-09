#!/usr/bin/env python3
import psycopg2
import sys

# タイムアウトを短くして、すぐに結果を得る
try:
    print("Connecting to PC-KEIBA Database...")
    print("Host: 172.25.160.1")
    print("Port: 5432")
    print("Database: pckeiba")
    
    conn = psycopg2.connect(
        host="172.25.160.1",
        port=5432,
        database="pckeiba", 
        user="postgres",
        password="postgres",
        connect_timeout=5
    )
    
    print("✅ 接続成功！")
    
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM nvd_ra")
    count = cur.fetchone()[0]
    print(f"nvd_ra テーブルのレコード数: {count:,}")
    
    cur.close()
    conn.close()
    
except psycopg2.OperationalError as e:
    print(f"❌ 接続エラー: {e}")
    print("\n対処方法:")
    print("1. Windows Defenderファイアウォールで「受信の規則」を追加")
    print("   - ポート: 5432")
    print("   - プロトコル: TCP")
    print("   - プロファイル: すべて")
    print("2. または一時的にWindows Defenderファイアウォールを無効化")
except Exception as e:
    print(f"エラー: {e}")