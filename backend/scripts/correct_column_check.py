#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
jvd_umテーブルの正しいカラム構造を確認
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

def check_correct_columns():
    """正しいカラム構造を確認"""
    
    print("=" * 80)
    print("🔍 jvd_umテーブルの正しいカラム構造確認")
    print("=" * 80)
    
    try:
        conn = psycopg2.connect(**CONNECTION_PARAMS)
        cur = conn.cursor()
        
        # 1. 全カラムを順番通りに表示
        print("\n【jvd_umテーブルの全カラム（順番通り）】")
        print("-" * 60)
        
        cur.execute("""
            SELECT 
                ordinal_position,
                column_name,
                data_type
            FROM information_schema.columns
            WHERE table_name = 'jvd_um'
            ORDER BY ordinal_position
        """)
        
        columns = cur.fetchall()
        for pos, name, dtype in columns:
            if 'ketto' in name or 'bamei' in name or 'chichi' in name or 'haha' in name:
                print(f"  {pos:3}: {name:40} | {dtype}")
        
        # 2. 実際のデータで確認
        print("\n【実際のデータで構造確認】")
        print("-" * 60)
        
        cur.execute("""
            SELECT 
                ketto_toroku_bango,
                bamei,
                ketto_joho_01a,
                ketto_joho_01b,
                ketto_joho_02a,
                ketto_joho_02b,
                ketto_joho_03a,
                ketto_joho_03b
            FROM jvd_um
            WHERE ketto_toroku_bango = '2022104616'
        """)
        
        result = cur.fetchone()
        if result:
            print(f"血統登録番号: {result[0]}")
            print(f"馬名: {result[1]}")
            print(f"ketto_joho_01a: {result[2]}")
            print(f"ketto_joho_01b: {result[3]}")
            print(f"ketto_joho_02a: {result[4]}")
            print(f"ketto_joho_02b: {result[5]}")
            print(f"ketto_joho_03a: {result[6]}")
            print(f"ketto_joho_03b: {result[7]}")
        
        # 3. パターン分析
        print("\n【データパターン分析】")
        print("-" * 60)
        
        cur.execute("""
            SELECT 
                CASE 
                    WHEN ketto_joho_01a LIKE '112%' THEN '112系（種牡馬コード？）'
                    WHEN ketto_joho_01a LIKE '122%' THEN '122系（牝馬コード？）'
                    ELSE 'その他'
                END as pattern,
                COUNT(*)
            FROM jvd_um
            WHERE ketto_joho_01a IS NOT NULL
            GROUP BY pattern
        """)
        
        for row in cur.fetchall():
            print(f"  {row[0]}: {row[1]}件")
        
        # 4. 正しい理解を確認
        print("\n【正しい理解の確認】")
        print("-" * 60)
        
        print("予想される構造:")
        print("  ketto_joho_01a = 父馬コード（112で始まる）")
        print("  ketto_joho_01b = 父馬名")
        print("  ketto_joho_02a = 母父コード（122で始まる）")
        print("  ketto_joho_02b = 母父名")
        
        # 実際に確認
        cur.execute("""
            SELECT 
                ketto_joho_01a,
                ketto_joho_01b,
                LENGTH(ketto_joho_01b),
                ketto_joho_02a,
                ketto_joho_02b
            FROM jvd_um
            WHERE ketto_joho_01b IS NOT NULL
            AND ketto_joho_01b != ''
            LIMIT 5
        """)
        
        print("\n実際のデータ:")
        for row in cur.fetchall():
            print(f"  01a: {row[0]}")
            print(f"  01b: {row[1][:30]} (長さ: {row[2]})")
            print(f"  02a: {row[3]}")
            print(f"  02b: {row[4][:30] if row[4] else 'NULL'}")
            print()
        
        cur.close()
        conn.close()
        
    except Exception as e:
        import traceback
        print(f"エラー: {e}")
        print(f"詳細: {traceback.format_exc()}")

if __name__ == "__main__":
    check_correct_columns()