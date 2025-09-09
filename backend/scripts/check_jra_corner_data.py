#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JRAデータのコーナー順位データ確認
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

def check_corner_data():
    """JRAテーブルのコーナー順位データを確認"""
    
    print("=" * 80)
    print("JRAデータのコーナー順位確認")
    print("=" * 80)
    
    try:
        conn = psycopg2.connect(**CONNECTION_PARAMS)
        cur = conn.cursor()
        
        # jvd_seテーブルの実際のカラム名を確認
        print("\n1. jvd_seテーブルのカラム確認:")
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'jvd_se' 
            AND column_name LIKE '%corner%'
            ORDER BY column_name
        """)
        
        corner_columns = cur.fetchall()
        if corner_columns:
            print("コーナー関連カラム:")
            for col in corner_columns:
                print(f"  - {col[0]}")
        else:
            print("❌ cornerカラムが見つかりません")
        
        # 実際のデータを確認（コーナー順位がある馬を探す）
        print("\n2. 実際のコーナー順位データ確認:")
        
        # まずはcorner_1〜4のカラムがあるか確認
        test_query = """
        SELECT 
            bamei,
            kaisai_nen,
            kaisai_tsukihi,
            keibajo_code,
            race_bango,
            corner_1,
            corner_2,
            corner_3,
            corner_4,
            kakutei_chakujun
        FROM jvd_se
        WHERE kaisai_nen = '2024'
        AND corner_1 IS NOT NULL 
        AND corner_1 != '00'
        AND corner_1 != ''
        LIMIT 10
        """
        
        try:
            cur.execute(test_query)
            results = cur.fetchall()
            
            if results:
                print("✅ コーナー順位データが存在する馬:")
                for row in results:
                    print(f"\n  馬名: {row[0]}")
                    print(f"  日付: {row[1]}年{row[2]}")
                    print(f"  場所: {row[3]} {row[4]}R")
                    print(f"  コーナー: 1角={row[5]}, 2角={row[6]}, 3角={row[7]}, 4角={row[8]}")
                    print(f"  着順: {row[9]}")
            else:
                print("⚠️ 2024年のデータでコーナー順位が入っているものが見つかりません")
                
                # NULLか空文字の割合を確認
                print("\n3. コーナーデータの状態を統計:")
                cur.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN corner_1 IS NULL THEN 1 ELSE 0 END) as corner1_null,
                    SUM(CASE WHEN corner_1 = '00' THEN 1 ELSE 0 END) as corner1_00,
                    SUM(CASE WHEN corner_1 = '' THEN 1 ELSE 0 END) as corner1_empty,
                    SUM(CASE WHEN corner_1 IS NOT NULL AND corner_1 != '00' AND corner_1 != '' THEN 1 ELSE 0 END) as corner1_valid
                FROM jvd_se
                WHERE kaisai_nen IN ('2023', '2024')
                """)
                
                stats = cur.fetchone()
                if stats:
                    total = stats[0]
                    print(f"  総レース数: {total:,}")
                    print(f"  corner_1がNULL: {stats[1]:,} ({stats[1]/total*100:.1f}%)")
                    print(f"  corner_1が'00': {stats[2]:,} ({stats[2]/total*100:.1f}%)")
                    print(f"  corner_1が空文字: {stats[3]:,} ({stats[3]/total*100:.1f}%)")
                    print(f"  corner_1に有効値: {stats[4]:,} ({stats[4]/total*100:.1f}%)")
                    
        except Exception as e:
            print(f"エラー: {e}")
            
            # カラム名が異なる可能性があるので、別の名前で試す
            print("\n4. 別のカラム名で確認:")
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'jvd_se' 
                AND (column_name LIKE '%juni%' OR column_name LIKE '%tsuka%' OR column_name LIKE '%order%')
                ORDER BY column_name
                LIMIT 20
            """)
            
            other_columns = cur.fetchall()
            if other_columns:
                print("順位関連かもしれないカラム:")
                for col in other_columns:
                    print(f"  - {col[0]}")
        
        # JRA（中央）と地方でテーブル構造が違う可能性
        print("\n5. JRA専用テーブルの確認:")
        cur.execute("""
            SELECT DISTINCT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE 'jvd_%'
            ORDER BY table_name
            LIMIT 10
        """)
        
        jra_tables = cur.fetchall()
        print("JRA関連テーブル:")
        for table in jra_tables:
            print(f"  - {table[0]}")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        import traceback
        print(f"エラー: {e}")
        print(f"詳細: {traceback.format_exc()}")

if __name__ == "__main__":
    check_corner_data()