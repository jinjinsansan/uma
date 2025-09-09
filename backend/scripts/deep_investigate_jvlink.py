#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JV-LINKデータ構造の徹底調査
PC-KEIBAにも必ず種牡馬マスターがあるはず
"""

import psycopg2
import sys
import io

# Windows環境での文字化け対策
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# データベース接続情報
CONNECTION_PARAMS = {
    "host": "172.25.160.1",
    "port": "5432",
    "database": "pckeiba",
    "user": "postgres",
    "password": "postgres"
}

def deep_investigate():
    """JV-LINKデータ構造を徹底調査"""
    
    print("=" * 80)
    print("🔍 JV-LINKデータ構造の徹底調査")
    print("=" * 80)
    
    try:
        conn = psycopg2.connect(**CONNECTION_PARAMS)
        cur = conn.cursor()
        
        # 1. 全テーブルをリストアップ
        print("\n【1. 全JVDテーブル一覧】")
        print("-" * 60)
        
        cur.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name LIKE 'jvd_%'
            ORDER BY table_name
        """)
        
        all_tables = cur.fetchall()
        print(f"JVDテーブル総数: {len(all_tables)}")
        for table in all_tables:
            print(f"  {table[0]}")
        
        # 2. 血統関連テーブルを特定
        print("\n【2. 血統関連テーブルの詳細調査】")
        print("-" * 60)
        
        # jvd_um（馬マスター）の構造確認
        cur.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'jvd_um'
            AND (
                column_name LIKE '%chichi%'
                OR column_name LIKE '%haha%'
                OR column_name LIKE '%father%'
                OR column_name LIKE '%mother%'
                OR column_name LIKE '%sire%'
                OR column_name LIKE '%dam%'
                OR column_name LIKE '%bamei%'
            )
            ORDER BY column_name
        """)
        
        print("\njvd_umの血統関連カラム:")
        for row in cur.fetchall():
            print(f"  {row[0]:30} | {row[1]}")
        
        # 3. jvd_hs（繁殖馬？）テーブルを確認
        print("\n【3. jvd_hs（繁殖馬）テーブル調査】")
        print("-" * 60)
        
        cur.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'jvd_hs'
            ORDER BY column_name
            LIMIT 20
        """)
        
        columns = cur.fetchall()
        if columns:
            print("jvd_hsテーブルのカラム:")
            for col in columns:
                print(f"  - {col[0]}")
            
            # サンプルデータ確認
            cur.execute("""
                SELECT *
                FROM jvd_hs
                LIMIT 3
            """)
            
            results = cur.fetchall()
            if results:
                print("\njvd_hsのサンプルデータ:")
                for i, row in enumerate(results):
                    print(f"  レコード{i+1}: {str(row[:5])[:100]}...")
        
        # 4. jvd_sk（産駒？）テーブルを確認
        print("\n【4. jvd_sk（産駒）テーブル調査】")
        print("-" * 60)
        
        cur.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'jvd_sk'
            ORDER BY column_name
            LIMIT 20
        """)
        
        columns = cur.fetchall()
        if columns:
            print("jvd_skテーブルのカラム:")
            for col in columns:
                print(f"  - {col[0]}")
        
        # 5. 血統コードと馬名の対応を探す
        print("\n【5. 血統コードと馬名の対応調査】")
        print("-" * 60)
        
        # 父コード1120002565の正体を探す
        target_code = '1120002565'
        print(f"\nコード {target_code} を調査:")
        
        # 各テーブルで検索
        search_tables = ['jvd_um', 'jvd_hs', 'jvd_sk']
        
        for table in search_tables:
            # カラムリスト取得
            cur.execute(f"""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = '{table}'
                AND data_type LIKE '%char%'
            """)
            
            columns = [col[0] for col in cur.fetchall()]
            
            # 各カラムで検索
            for col in columns[:10]:  # 最初の10カラムのみ
                try:
                    cur.execute(f"""
                        SELECT {col}, COUNT(*)
                        FROM {table}
                        WHERE {col} = %s
                        GROUP BY {col}
                    """, (target_code,))
                    
                    result = cur.fetchone()
                    if result:
                        print(f"  ✅ {table}.{col}で発見: {result}")
                except:
                    pass
        
        # 6. 馬名変換の可能性を探る
        print("\n【6. 血統番号から馬名への変換】")
        print("-" * 60)
        
        # ketto_joho_01bが馬名なら、同じ構造で父馬名もあるはず
        cur.execute("""
            SELECT 
                ketto_toroku_bango,
                bamei,
                ketto_joho_01a,
                ketto_joho_01b,
                ketto_joho_02a
            FROM jvd_um
            WHERE ketto_joho_01a = '1120002565'
            LIMIT 5
        """)
        
        results = cur.fetchall()
        if results:
            print("コード1120002565を父に持つ馬:")
            for row in results:
                print(f"  馬名: {row[1]}")
                print(f"    父コード: {row[2]}")
                print(f"    母名: {row[3]}")
                print(f"    母父コード: {row[4]}")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        import traceback
        print(f"エラー: {e}")
        print(f"詳細: {traceback.format_exc()}")

if __name__ == "__main__":
    deep_investigate()