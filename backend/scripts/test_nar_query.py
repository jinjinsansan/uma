#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
地方競馬クエリテスト
"""

import psycopg2
import sys
import io
import traceback

# Windows環境での文字化け対策
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

CONNECTION_PARAMS = {
    "host": "172.25.160.1",
    "port": "5432",
    "database": "pckeiba",
    "user": "postgres",
    "password": "postgres"
}

def test_simple_query():
    """シンプルなクエリでテーブル構造を確認"""
    
    try:
        conn = psycopg2.connect(**CONNECTION_PARAMS)
        cur = conn.cursor()
        
        # まずテーブル構造を確認
        print("nvd_se のカラム確認:")
        cur.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'nvd_se'
            LIMIT 10
        """)
        
        for row in cur.fetchall():
            print(f"  {row[0]}: {row[1]}")
        
        # サンプルデータ取得
        print("\nnvd_seのサンプルデータ:")
        cur.execute("""
            SELECT 
                bamei,
                kaisai_nen,
                kaisai_tsukihi,
                keibajo_code,
                race_bango
            FROM nvd_se
            WHERE keibajo_code = '44'
                AND kaisai_nen = '2024'
            LIMIT 3
        """)
        
        for row in cur.fetchall():
            print(f"  馬名: {row[0]}, 年: {row[1]}, 月日: {row[2]}, 場: {row[3]}, R: {row[4]}")
        
        # kaisai_tsukihiの形式を確認
        print("\nkaisai_tsukihiの形式確認:")
        cur.execute("""
            SELECT DISTINCT 
                kaisai_tsukihi,
                LENGTH(kaisai_tsukihi) as len
            FROM nvd_se
            WHERE keibajo_code = '44'
                AND kaisai_nen = '2024'
            LIMIT 5
        """)
        
        for row in cur.fetchall():
            print(f"  値: {row[0]}, 長さ: {row[1]}")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"エラー: {e}")
        print(traceback.format_exc())

def test_full_query():
    """フルクエリのテスト"""
    
    try:
        conn = psycopg2.connect(**CONNECTION_PARAMS)
        cur = conn.cursor()
        
        query = """
        SELECT 
            se.bamei,
            se.kaisai_nen,
            se.kaisai_tsukihi,
            se.kakutei_chakujun
        FROM nvd_se se
        WHERE se.keibajo_code = '44'
            AND se.kaisai_nen = '2024'
            AND se.bamei IS NOT NULL
        LIMIT 5
        """
        
        print("基本クエリ実行:")
        cur.execute(query)
        
        for row in cur.fetchall():
            print(f"  {row}")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"エラー: {e}")
        print(traceback.format_exc())

if __name__ == "__main__":
    test_simple_query()
    print("\n" + "="*60 + "\n")
    test_full_query()