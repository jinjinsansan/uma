#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JRAデータ構造の完全調査 - 正確なナレッジファイル作成のため
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

def investigate_structure():
    """JRAデータ構造の完全調査"""
    
    print("=" * 80)
    print("🔍 JRAデータ構造の完全調査")
    print("=" * 80)
    
    try:
        conn = psycopg2.connect(**CONNECTION_PARAMS)
        cur = conn.cursor()
        
        # 1. 競馬場コードの調査（国内のみ抽出するため）
        print("\n【1. 競馬場コードの分布】")
        print("-" * 60)
        
        cur.execute("""
            SELECT 
                keibajo_code,
                COUNT(*) as count,
                MIN(kaisai_nen) as min_year,
                MAX(kaisai_nen) as max_year
            FROM jvd_se
            WHERE kaisai_nen = '2024'
            GROUP BY keibajo_code
            ORDER BY count DESC
            LIMIT 20
        """)
        
        print("競馬場コード | レース数 | 最小年 | 最大年")
        for row in cur.fetchall():
            print(f"  {row[0]:10} | {row[1]:8,} | {row[2]} | {row[3]}")
        
        print("\n※ 国内競馬場コード: 01〜10")
        print("※ 海外競馬場コード: A0〜Z9など")
        
        # 2. 血統情報の構造調査
        print("\n【2. 血統情報の構造（jvd_um）】")
        print("-" * 60)
        
        cur.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'jvd_um'
            AND column_name LIKE '%ketto%' OR column_name LIKE '%joho%'
            ORDER BY column_name
            LIMIT 20
        """)
        
        print("カラム名 | データ型")
        for row in cur.fetchall():
            print(f"  {row[0]} | {row[1]}")
        
        # 3. 血統マスターテーブルの存在確認
        print("\n【3. 血統マスターテーブルの確認】")
        print("-" * 60)
        
        cur.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND (table_name LIKE '%ketto%' OR table_name LIKE '%pedigree%' 
                 OR table_name LIKE '%sire%' OR table_name LIKE '%uma%master%')
            ORDER BY table_name
        """)
        
        tables = cur.fetchall()
        if tables:
            print("血統関連テーブル:")
            for table in tables:
                print(f"  - {table[0]}")
        
        # 4. 実際の血統データサンプル（コードと名前の関係）
        print("\n【4. 血統データのサンプル（2024年の有効データ）】")
        print("-" * 60)
        
        cur.execute("""
            SELECT 
                se.bamei,
                se.ketto_toroku_bango,
                um.ketto_joho_01a as sire_code,
                um.ketto_joho_01b as dam_code,
                um.ketto_joho_02a as broodmare_sire_code
            FROM jvd_se se
            JOIN jvd_um um ON se.ketto_toroku_bango = um.ketto_toroku_bango
            WHERE se.kaisai_nen = '2024'
            AND se.keibajo_code IN ('01','02','03','04','05','06','07','08','09','10')
            AND se.ketto_toroku_bango != '0000000000'
            AND um.ketto_joho_01a IS NOT NULL
            LIMIT 3
        """)
        
        results = cur.fetchall()
        for row in results:
            print(f"\n馬名: {row[0].strip()}")
            print(f"  血統登録番号: {row[1]}")
            print(f"  父コード: {row[2]}")
            print(f"  母コード: {row[3]}")
            print(f"  母父コード: {row[4]}")
        
        # 5. 馬齢の計算方法確認
        print("\n【5. 馬齢計算のためのデータ】")
        print("-" * 60)
        
        cur.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN um.seinengappi IS NOT NULL THEN 1 ELSE 0 END) as with_birthdate
            FROM jvd_se se
            LEFT JOIN jvd_um um ON se.ketto_toroku_bango = um.ketto_toroku_bango
            WHERE se.kaisai_nen = '2024'
            AND se.keibajo_code IN ('01','02','03','04','05','06','07','08','09','10')
        """)
        
        result = cur.fetchone()
        print(f"総レース数: {result[0]:,}")
        print(f"生年月日データあり: {result[1]:,} ({result[1]/result[0]*100:.1f}%)")
        
        # 6. 重要フィールドの有効率（国内のみ）
        print("\n【6. 国内レースのデータ品質】")
        print("-" * 60)
        
        fields = ['tansho_odds', 'corner_3', 'corner_4', 'soha_time', 'bataiju']
        
        for field in fields:
            cur.execute(f"""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN {field} IS NOT NULL 
                             AND {field} != '' 
                             AND {field} != '00' 
                             AND {field} != '000' 
                             AND {field} != '0000' 
                        THEN 1 ELSE 0 END) as valid
                FROM jvd_se
                WHERE kaisai_nen = '2024'
                AND keibajo_code IN ('01','02','03','04','05','06','07','08','09','10')
            """)
            
            result = cur.fetchone()
            valid_rate = (result[1] / result[0] * 100) if result[0] > 0 else 0
            print(f"{field:20}: {valid_rate:.1f}% 有効")
        
        # 7. 競馬場名のマッピング
        print("\n【7. 競馬場コード → 名前のマッピング】")
        print("-" * 60)
        
        keibajo_map = {
            '01': '札幌', '02': '函館', '03': '福島', '04': '新潟',
            '05': '東京', '06': '中山', '07': '中京', '08': '京都',
            '09': '阪神', '10': '小倉'
        }
        
        for code, name in keibajo_map.items():
            print(f"  {code}: {name}")
        
        cur.close()
        conn.close()
        
        return True
        
    except Exception as e:
        import traceback
        print(f"エラー: {e}")
        print(f"詳細: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    investigate_structure()