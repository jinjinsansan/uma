#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
血統情報の解決方法を調査
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

def investigate_pedigree():
    """血統情報の構造と解決方法を調査"""
    
    print("=" * 80)
    print("🔍 血統情報の解決方法調査")
    print("=" * 80)
    
    try:
        conn = psycopg2.connect(**CONNECTION_PARAMS)
        cur = conn.cursor()
        
        # 1. 血統コードの実態を確認
        print("\n【1. 血統データの実態確認】")
        print("-" * 60)
        
        cur.execute("""
            SELECT 
                um.ketto_toroku_bango,
                um.ketto_joho_01a as sire_code,
                um.ketto_joho_01b as dam_name,
                um.ketto_joho_02a as broodmare_sire_code
            FROM jvd_um um
            WHERE um.ketto_toroku_bango IN (
                SELECT DISTINCT ketto_toroku_bango 
                FROM jvd_se 
                WHERE kaisai_nen = '2024' 
                AND keibajo_code IN ('01','02','03','04','05','06','07','08','09','10')
                LIMIT 5
            )
        """)
        
        print("血統登録番号 | 父コード | 母名 | 母父コード")
        for row in cur.fetchall():
            print(f"{row[0]} | {row[1]} | {row[2][:20] if row[2] else 'NULL'} | {row[3]}")
        
        print("\n※ 父と母父はコード、母は馬名で保存されている！")
        
        # 2. 血統マスターテーブルを探す
        print("\n【2. 血統マスターテーブルの探索】")
        print("-" * 60)
        
        # 全テーブルから血統関連を探す
        cur.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND (
                table_name LIKE '%stallion%' 
                OR table_name LIKE '%sire%'
                OR table_name LIKE '%blood%'
                OR table_name LIKE '%pedigree%'
                OR table_name LIKE '%master%'
                OR table_name LIKE '%uma%'
                OR table_name LIKE '%horse%'
            )
            ORDER BY table_name
        """)
        
        tables = cur.fetchall()
        if tables:
            print("血統関連の可能性があるテーブル:")
            for table in tables:
                print(f"  - {table[0]}")
        
        # 3. jvd_umテーブルの全カラムを確認
        print("\n【3. jvd_umテーブルの全カラム確認】")
        print("-" * 60)
        
        cur.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'jvd_um'
            AND (
                column_name LIKE '%name%'
                OR column_name LIKE '%mei%'
                OR column_name LIKE '%sire%'
                OR column_name LIKE '%dam%'
            )
            ORDER BY column_name
            LIMIT 20
        """)
        
        columns = cur.fetchall()
        if columns:
            print("名前関連のカラム:")
            for col in columns:
                print(f"  - {col[0]}")
        
        # 4. 血統コードから馬名への変換可能性を調査
        print("\n【4. 血統コードの解析】")
        print("-" * 60)
        
        # 父コードのパターンを分析
        cur.execute("""
            SELECT 
                SUBSTRING(ketto_joho_01a, 1, 3) as prefix,
                COUNT(*) as count
            FROM jvd_um
            WHERE ketto_joho_01a IS NOT NULL
            AND ketto_joho_01a != ''
            GROUP BY SUBSTRING(ketto_joho_01a, 1, 3)
            ORDER BY count DESC
            LIMIT 5
        """)
        
        print("父コードのプレフィックス分布:")
        for row in cur.fetchall():
            print(f"  {row[0]}: {row[1]}件")
        
        # 5. 他のテーブルとの結合可能性
        print("\n【5. 種牡馬データの探索】")
        print("-" * 60)
        
        # jvd_btテーブル（種牡馬？）を確認
        cur.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'jvd_bt'
            ORDER BY column_name
            LIMIT 10
        """)
        
        columns = cur.fetchall()
        if columns:
            print("jvd_btテーブルのカラム:")
            for col in columns:
                print(f"  - {col[0]}")
        
        # 6. 実際のデータで母名が正しいか確認
        print("\n【6. 母名データの確認（これは使える！）】")
        print("-" * 60)
        
        cur.execute("""
            SELECT 
                se.bamei as horse_name,
                um.ketto_joho_01b as dam_name
            FROM jvd_se se
            JOIN jvd_um um ON se.ketto_toroku_bango = um.ketto_toroku_bango
            WHERE se.kaisai_nen = '2024'
            AND se.keibajo_code = '05'
            AND um.ketto_joho_01b IS NOT NULL
            AND um.ketto_joho_01b != ''
            LIMIT 5
        """)
        
        print("馬名 | 母名")
        for row in cur.fetchall():
            horse = row[0].strip() if row[0] else ''
            dam = row[1].strip() if row[1] else ''
            print(f"{horse[:20]:20} | {dam[:20]}")
        
        # 7. 解決策の提案
        print("\n" + "=" * 80)
        print("💡 【解決策の提案】")
        print("=" * 80)
        print("\n1. 母名は既に馬名で保存されている → そのまま使用可能")
        print("2. 父と母父はコード形式 → 以下の方法で対応：")
        print("   a) コードのまま保存（分析には使えないが動作は可能）")
        print("   b) 頻出種牡馬のみ手動マッピング作成")
        print("   c) MySQLの既存データから種牡馬マスターを作成")
        print("   d) 血統情報は諦めて空欄のまま（現実的）")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        import traceback
        print(f"エラー: {e}")
        print(f"詳細: {traceback.format_exc()}")

if __name__ == "__main__":
    investigate_pedigree()