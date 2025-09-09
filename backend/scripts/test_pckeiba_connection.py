#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PC-KEIBA Database接続テスト（シンプル版）
"""

import psycopg2
import sys
import io

# Windows環境での文字化け対策
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 複数の接続先を試す
hosts_to_try = [
    "172.25.160.1",   # 典型的なWSL2 Windows host IP
    "172.17.176.1",   # 別の可能性
    "172.24.80.1",    # 別の可能性
    "172.22.224.1",   # 別の可能性
    "host.docker.internal",  # Docker用
    "127.0.0.1",      # localhost
]

print("PC-KEIBA Database接続テスト")
print("=" * 50)

for host in hosts_to_try:
    print(f"\n試行中: {host}:5432 ...", end=" ")
    try:
        conn = psycopg2.connect(
            host=host,
            port="5432",
            database="pckeiba",
            user="postgres",
            password="postgres",
            connect_timeout=3  # 3秒でタイムアウト
        )
        print("✅ 成功!")
        print(f"\n接続成功！ホスト: {host}")
        
        # テーブル一覧を取得
        cursor = conn.cursor()
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
                AND table_name LIKE 'nvd_%'
            ORDER BY table_name
            LIMIT 10
        """)
        
        tables = cursor.fetchall()
        print(f"\n地方競馬テーブル一覧（最初の10個）:")
        for table in tables:
            print(f"  - {table[0]}")
            
        cursor.close()
        conn.close()
        
        print(f"\n✅ 接続可能なホスト: {host}")
        print(f"以下の接続情報を使用してください:")
        print(f'CONNECTION_PARAMS = {{')
        print(f'    "host": "{host}",')
        print(f'    "port": "5432",')
        print(f'    "database": "pckeiba",')
        print(f'    "user": "postgres",')
        print(f'    "password": "postgres"')
        print(f'}}')
        
        break
        
    except psycopg2.OperationalError as e:
        if "timeout" in str(e).lower():
            print("❌ タイムアウト")
        else:
            print(f"❌ 失敗: {str(e)[:50]}...")
    except Exception as e:
        print(f"❌ エラー: {str(e)[:50]}...")
else:
    print("\n\n❌ すべての接続先で失敗しました。")
    print("\n確認事項:")
    print("1. PC-KEIBA DatabaseがWindows側で起動していますか？")
    print("2. PostgreSQLサービスが実行中ですか？")
    print("3. Windows Defenderファイアウォールでポート5432を許可していますか？")
    print("4. PostgreSQLのpostgresql.confでlisten_addresses = '*'が設定されていますか？")