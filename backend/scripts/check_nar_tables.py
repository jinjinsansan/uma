#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PC-KEIBA Database 地方競馬テーブル確認
"""

import psycopg2
import sys
import io

# Windows環境での文字化け対策
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

CONNECTION_PARAMS = {
    "host": "172.25.160.1",
    "port": "5432",
    "database": "pckeiba",
    "user": "postgres",
    "password": "postgres"
}

def main():
    print("PC-KEIBA Database テーブル確認")
    print("=" * 60)
    
    try:
        conn = psycopg2.connect(**CONNECTION_PARAMS)
        cur = conn.cursor()
        
        # すべてのテーブルを取得
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        tables = cur.fetchall()
        print(f"総テーブル数: {len(tables)}")
        print("\nテーブル一覧:")
        
        # nvd_で始まるテーブルを探す
        nvd_tables = []
        for table in tables:
            table_name = table[0]
            print(f"  - {table_name}")
            if table_name.startswith('nvd_'):
                nvd_tables.append(table_name)
        
        print(f"\n'nvd_'で始まるテーブル数: {len(nvd_tables)}")
        
        if nvd_tables:
            print("\nnvd_テーブル一覧:")
            for table in nvd_tables:
                # レコード数を取得
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                count = cur.fetchone()[0]
                print(f"  - {table}: {count:,}件")
        
        # 南関東のデータを確認
        print("\n南関東データ確認:")
        test_tables = ['nvd_ra', 'nvd_se', 'ra', 'se']
        
        for table in test_tables:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {table} LIMIT 1")
                count = cur.fetchone()[0]
                print(f"  {table}テーブル: {count:,}件")
            except:
                print(f"  {table}テーブル: 存在しません")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"エラー: {e}")

if __name__ == "__main__":
    main()