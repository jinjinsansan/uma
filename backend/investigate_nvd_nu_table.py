#!/usr/bin/env python3
"""nvd_nuテーブルの調査とシーソーゲームの正しいデータ取得"""

import psycopg2
import sys

CONNECTION_PARAMS = {
    "host": "172.25.160.1",
    "port": "5432",
    "database": "pckeiba",
    "user": "postgres",
    "password": "postgres"
}

def investigate_nvd_nu_table():
    print("=" * 80)
    print("nvd_nuテーブル調査とシーソーゲーム検索")
    print("=" * 80)
    
    try:
        conn = psycopg2.connect(**CONNECTION_PARAMS)
        cur = conn.cursor()
        
        # 1. テーブル構造の確認
        print("\n【1. 馬関連テーブルの確認】")
        cur.execute("""
            SELECT table_name, table_type
            FROM information_schema.tables 
            WHERE table_name IN ('jvd_um', 'nvd_um', 'nvd_nu')
            ORDER BY table_name
        """)
        
        tables = cur.fetchall()
        for table in tables:
            print(f"  {table[0]}: {table[1]}")
            
            # カラム数を確認
            cur.execute(f"""
                SELECT COUNT(*) 
                FROM information_schema.columns 
                WHERE table_name = '{table[0]}'
            """)
            col_count = cur.fetchone()[0]
            print(f"    カラム数: {col_count}")
        
        # 2. nvd_nuテーブルの構造確認
        print("\n【2. nvd_nuテーブルの主要カラム】")
        cur.execute("""
            SELECT column_name, data_type, character_maximum_length
            FROM information_schema.columns
            WHERE table_name = 'nvd_nu'
                AND column_name IN (
                    'ketto_toroku_bango', 'bamei', 'seibetsu_code',
                    'seinengappi', 'ketto_joho_01b', 'ketto_joho_02b'
                )
            ORDER BY ordinal_position
        """)
        
        columns = cur.fetchall()
        if columns:
            for col in columns:
                print(f"  {col[0]}: {col[1]} ({col[2]})")
        else:
            print("  nvd_nuテーブルが存在しないか、カラムが異なります")
        
        # 3. シーソーゲーム（2022110145）をnvd_nuで検索
        print("\n【3. nvd_nuテーブルでシーソーゲーム検索】")
        ketto_no = '2022110145'
        
        # nvd_nuテーブルが存在するか確認
        cur.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = 'nvd_nu'
            )
        """)
        
        if cur.fetchone()[0]:
            cur.execute("""
                SELECT 
                    ketto_toroku_bango,
                    bamei,
                    seibetsu_code,
                    seinengappi
                FROM nvd_nu
                WHERE ketto_toroku_bango = %s
            """, (ketto_no,))
            
            horse = cur.fetchone()
            if horse:
                print(f"  ✅ 発見！")
                print(f"  血統登録番号: {horse[0]}")
                print(f"  馬名: {horse[1].strip()}")
                print(f"  性別: {horse[2]}")
                print(f"  生年月日: {horse[3]}")
            else:
                print(f"  ❌ nvd_nuテーブルに{ketto_no}は存在しません")
        else:
            print("  ❌ nvd_nuテーブルが存在しません")
        
        # 4. nvd_umとnvd_nuの両方でシーソーゲーム名検索
        print("\n【4. 馬名でシーソーゲームを検索（両テーブル）】")
        
        print("\n  nvd_umテーブル:")
        cur.execute("""
            SELECT ketto_toroku_bango, bamei, seinengappi
            FROM nvd_um
            WHERE bamei LIKE '%シーソーゲーム%'
            ORDER BY seinengappi DESC
            LIMIT 5
        """)
        
        horses_um = cur.fetchall()
        for horse in horses_um:
            print(f"    {horse[0]}: {horse[1].strip()} ({horse[2]})")
        
        # nvd_nuが存在する場合
        cur.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = 'nvd_nu'
            )
        """)
        
        if cur.fetchone()[0]:
            print("\n  nvd_nuテーブル:")
            cur.execute("""
                SELECT ketto_toroku_bango, bamei, seinengappi
                FROM nvd_nu
                WHERE bamei LIKE '%シーソーゲーム%'
                ORDER BY seinengappi DESC
                LIMIT 5
            """)
            
            horses_nu = cur.fetchall()
            for horse in horses_nu:
                print(f"    {horse[0]}: {horse[1].strip()} ({horse[2]})")
        
        # 5. 競馬場名の文字列フィールドを探す
        print("\n【5. 競馬場名の文字列フィールドを探索】")
        
        # nvd_raテーブルで競馬場名カラムを探す
        cur.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'nvd_ra'
                AND data_type LIKE 'character%'
                AND column_name LIKE '%ba%'
            ORDER BY column_name
        """)
        
        ba_columns = cur.fetchall()
        if ba_columns:
            print("  nvd_raテーブルの競馬場関連カラム:")
            for col in ba_columns:
                print(f"    {col[0]}")
                
                # サンプルデータを確認
                cur.execute(f"""
                    SELECT DISTINCT {col[0]}
                    FROM nvd_ra
                    WHERE {col[0]} IS NOT NULL
                        AND {col[0]} != ''
                    LIMIT 5
                """)
                samples = cur.fetchall()
                if samples:
                    print(f"      サンプル: {[s[0] for s in samples]}")
        
        # 6. 2025年6月11日のレースデータを直接確認
        print("\n【6. 2025年6月11日のレースデータ確認】")
        cur.execute("""
            SELECT DISTINCT
                se.keibajo_code,
                ra.keibajo_code as ra_keibajo,
                COUNT(*) as race_count
            FROM nvd_se se
            LEFT JOIN nvd_ra ra ON (
                se.kaisai_nen = ra.kaisai_nen
                AND se.kaisai_tsukihi = ra.kaisai_tsukihi
                AND se.keibajo_code = ra.keibajo_code
                AND se.race_bango = ra.race_bango
            )
            WHERE se.kaisai_nen = '2025'
                AND se.kaisai_tsukihi = '0611'
            GROUP BY se.keibajo_code, ra.keibajo_code
            ORDER BY race_count DESC
        """)
        
        races_0611 = cur.fetchall()
        keibajo_map = {'42': '大井', '43': '川崎', '44': '船橋', '45': '浦和'}
        
        for race in races_0611:
            ba_name = keibajo_map.get(race[0], f"不明({race[0]})")
            print(f"  競馬場コード{race[0]}({ba_name}): {race[2]}レース")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    investigate_nvd_nu_table()