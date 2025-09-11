#!/usr/bin/env python3
"""正しいシーソーゲームのレースデータ取得と競馬場マスタ調査"""

import psycopg2
import sys

CONNECTION_PARAMS = {
    "host": "172.25.160.1",
    "port": "5432",
    "database": "pckeiba",
    "user": "postgres",
    "password": "postgres"
}

def get_correct_seasaw_races():
    print("=" * 80)
    print("正しいシーソーゲーム（2022110145）のレースデータ取得")
    print("=" * 80)
    
    try:
        conn = psycopg2.connect(**CONNECTION_PARAMS)
        cur = conn.cursor()
        
        ketto_no = '2022110145'
        
        # 1. 競馬場マスタテーブルを探す
        print("\n【1. 競馬場マスタテーブルの探索】")
        cur.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_name LIKE '%keiba%' 
                OR table_name LIKE '%ba%'
                OR table_name LIKE '%jyo%'
                OR table_name LIKE '%place%'
                OR table_name LIKE '%course%'
            AND table_schema = 'public'
            ORDER BY table_name
            LIMIT 20
        """)
        
        tables = cur.fetchall()
        print("  競馬場関連の可能性があるテーブル:")
        for table in tables:
            print(f"    {table[0]}")
        
        # 2. nvd_kjテーブルやnvd_jyoテーブルを確認
        print("\n【2. 競馬場コードマスタの確認】")
        
        # nvd_kjがあるか確認
        cur.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'nvd_kj'
            ORDER BY ordinal_position
            LIMIT 10
        """)
        
        kj_columns = cur.fetchall()
        if kj_columns:
            print("  nvd_kjテーブルのカラム:")
            for col in kj_columns:
                print(f"    {col[0]}: {col[1]}")
                
            # サンプルデータ確認
            cur.execute("""
                SELECT *
                FROM nvd_kj
                WHERE keibajo_code IN ('42', '43', '44', '45')
                LIMIT 5
            """)
            
            samples = cur.fetchall()
            if samples:
                print("\n  南関東競馬場のサンプル:")
                for sample in samples:
                    print(f"    {sample}")
        
        # 3. シーソーゲームのレースデータ（正しい血統番号で）
        print("\n【3. シーソーゲームの全レースデータ】")
        
        # nvd_seから取得（競馬場コード付き）
        cur.execute("""
            SELECT 
                se.kaisai_nen,
                se.kaisai_tsukihi,
                se.keibajo_code,
                se.race_bango,
                se.kakutei_chakujun,
                se.kishumei_ryakusho,
                se.tansho_ninkijun,
                se.futan_juryo,
                se.soha_time
            FROM nvd_se se
            WHERE se.ketto_toroku_bango = %s
            ORDER BY se.kaisai_nen DESC, se.kaisai_tsukihi DESC
        """, (ketto_no,))
        
        races = cur.fetchall()
        print(f"  総レース数: {len(races)}件\n")
        
        # PC-KEIBAのGUIデータ（スクリーンショットから）
        gui_data = [
            ("2025/09/10", "川崎", "10R", "1着", "御神本訓"),
            ("2025/06/11", "大井", "16R", "6着", "御神本訓"),  # G1
            ("2025/05/04", "盛岡", "11R", "1着", "矢野貴之"),
            ("2025/04/14", "大井", "10R", "1着", "クアトロ"),
            ("2025/03/28", "大井", "9R", "2着", "矢野貴之"),
            ("2024/12/28", "京都", "13R", "10着", "M.デム"),
            ("2024/11/30", "中山", "12R", "12着", "三浦皇成"),
            ("2024/11/03", "福島", "15R", "6着", "菊沢一樹")
        ]
        
        print("  【SQLデータ vs PC-KEIBA GUI】")
        for i, race in enumerate(races):
            year = race[0]
            date = race[1]
            keibajo_code = race[2]
            race_no = race[3]
            chaku = race[4]
            jockey = race[5]
            
            print(f"\n  {i+1}. {year}年{date[:2]}月{date[2:]}日")
            print(f"     SQL: 競馬場コード{keibajo_code} {race_no}R {chaku}着 騎手:{jockey}")
            
            if i < len(gui_data):
                gui = gui_data[i]
                print(f"     GUI: {gui[1]} {gui[2]} {gui[3]} 騎手:{gui[4]}")
                
                # 競馬場コードと競馬場名のマッピングを推測
                if gui[1] == "川崎" and keibajo_code == "45":
                    print(f"     💡 45=川崎？（通常は43のはず）")
                elif gui[1] == "大井" and keibajo_code == "44":
                    print(f"     💡 44=大井？（通常は42のはず）")
                elif gui[1] == "盛岡" and keibajo_code == "35":
                    print(f"     💡 35=盛岡？（通常は50のはず）")
        
        # 4. 競馬場コードのカスタムマッピングを検証
        print("\n【4. 競馬場コードの実際のマッピング推測】")
        print("  PC-KEIBA独自のマッピング（推測）:")
        print("    44 → 大井（通常は42）")
        print("    45 → 川崎（通常は43）")
        print("    35 → 盛岡（通常は50）")
        print("    30-36 → JRA競馬場？")
        
        # 5. 6月11日のレース詳細確認
        print("\n【5. 2025年6月11日のレース詳細】")
        cur.execute("""
            SELECT 
                se.keibajo_code,
                se.race_bango,
                se.bamei,
                se.kakutei_chakujun,
                se.kishumei_ryakusho
            FROM nvd_se se
            WHERE se.kaisai_nen = '2025'
                AND se.kaisai_tsukihi = '0611'
                AND se.keibajo_code = '44'
                AND se.race_bango IN ('11', '16')
            ORDER BY se.race_bango, se.kakutei_chakujun
            LIMIT 20
        """)
        
        races_0611 = cur.fetchall()
        for race in races_0611:
            if 'シーソー' in race[2]:
                print(f"  ★ {race[1]}R: {race[2].strip()} {race[3]}着 騎手:{race[4]}")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    get_correct_seasaw_races()