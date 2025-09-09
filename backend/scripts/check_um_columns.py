#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import psycopg2
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

CONNECTION_PARAMS = {
    "host": "172.25.160.1",
    "port": "5432",
    "database": "pckeiba",
    "user": "postgres",
    "password": "postgres"
}

try:
    conn = psycopg2.connect(**CONNECTION_PARAMS)
    cur = conn.cursor()
    
    # nvd_umテーブルのカラムを確認
    print("nvd_umテーブルのカラム一覧:")
    cur.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'nvd_um'
        ORDER BY ordinal_position
    """)
    
    columns = cur.fetchall()
    for col in columns:
        print(f"  {col[0]}: {col[1]}")
    
    # 馬齢関連のカラムを探す
    print("\n馬齢・性別関連と思われるカラム:")
    for col in columns:
        if any(keyword in col[0].lower() for keyword in ['age', 'sei', 'nen', 'year', 'birth']):
            print(f"  {col[0]}: {col[1]}")
    
    # サンプルデータ確認
    print("\nサンプルデータ（1件）:")
    cur.execute("""
        SELECT ketto_toroku_bango, bamei, seibetsu_code
        FROM nvd_um
        LIMIT 1
    """)
    
    row = cur.fetchone()
    if row:
        print(f"  血統登録番号: {row[0]}")
        print(f"  馬名: {row[1]}")
        print(f"  性別: {row[2]}")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"エラー: {e}")