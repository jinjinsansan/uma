#!/usr/bin/env python3
"""シーソーゲーム（2022110145）の詳細データを確認"""

import psycopg2
import sys

CONNECTION_PARAMS = {
    "host": "172.25.160.1",
    "port": "5432",
    "database": "pckeiba",
    "user": "postgres",
    "password": "postgres"
}

def verify_seasaw_game_2022():
    print("=" * 80)
    print("シーソーゲーム（2022110145）詳細調査")
    print("=" * 80)
    
    try:
        conn = psycopg2.connect(**CONNECTION_PARAMS)
        cur = conn.cursor()
        
        ketto_no = '2022110145'
        
        # 1. 馬情報
        print("\n【1. 馬マスタ情報】")
        cur.execute("""
            SELECT 
                bamei,
                seibetsu_code,
                seinengappi,
                ketto_joho_01b as sire,
                ketto_joho_02b as broodmare_sire
            FROM nvd_um
            WHERE ketto_toroku_bango = %s
        """, (ketto_no,))
        
        horse = cur.fetchone()
        if horse:
            print(f"  馬名: {horse[0].strip()}")
            print(f"  血統登録番号: {ketto_no}")
            print(f"  性別: {horse[1]}")
            print(f"  生年月日: {horse[2]}")
            print(f"  父: {horse[3]}")
            print(f"  母父: {horse[4]}")
        
        # 2. 全レース成績
        print("\n【2. 全レース成績】")
        cur.execute("""
            SELECT 
                se.kaisai_nen,
                se.kaisai_tsukihi,
                se.keibajo_code,
                se.race_bango,
                se.kakutei_chakujun,
                se.kishumei_ryakusho,
                se.tansho_ninkijun,
                se.soha_time,
                se.kohan_3f
            FROM nvd_se se
            WHERE se.ketto_toroku_bango = %s
            ORDER BY se.kaisai_nen DESC, se.kaisai_tsukihi DESC
        """, (ketto_no,))
        
        races = cur.fetchall()
        print(f"  総レース数: {len(races)}件\n")
        
        keibajo_map = {
            '42': '大井', '43': '川崎', '44': '船橋', '45': '浦和',
            '50': '盛岡', '51': '水沢', '10': '東京', '11': '中山',
            '12': '福島'
        }
        
        # ネット競馬の情報
        netkeiba_data = [
            ("2025/06/11", "大井", "11R", "東京ダービー", "ダ2000", "3着", "御神本訓"),
            ("2025/05/04", "盛岡", "12R", "ダイヤモンドC", "ダ1800", "1着", "矢野貴之"),
            ("2025/04/14", "大井", "7R", "クラシックチャレンジ", "ダ1800", "2着", "クアトロ"),
            ("2025/03/28", "大井", "5R", "マトバダンス賞", "ダ1600", "1着", "矢野貴之"),
            ("2024/12/28", "京都", "9R", "2歳1勝クラス", "ダ1800", "12着", "デムーロ"),
            ("2024/11/30", "中山", "1R", "葉牡丹賞", "芝2000", "8着", "三浦皇成"),
            ("2024/11/03", "福島", "2R", "2歳新馬", "ダ1700", "1着", "菊沢一樹")
        ]
        
        print("  【PostgreSQLデータ】")
        for i, race in enumerate(races, 1):
            year = race[0]
            date = race[1]
            keibajo_code = race[2]
            race_no = race[3]
            chaku = race[4]
            jockey = race[5]
            ninki = race[6]
            
            # レース詳細情報を取得
            cur.execute("""
                SELECT kyori, track_code, babajotai_code_dirt, zenhan_3f
                FROM nvd_ra
                WHERE kaisai_nen = %s 
                    AND kaisai_tsukihi = %s
                    AND keibajo_code = %s
                    AND race_bango = %s
            """, (year, date, keibajo_code, race_no))
            
            race_info = cur.fetchone()
            
            ba_name = keibajo_map.get(keibajo_code, f"不明({keibajo_code})")
            
            print(f"\n  {i}. {year}年{date[:2]}月{date[2:]}日 {ba_name}({keibajo_code}) {race_no}R")
            if race_info:
                track_type = "ダート" if race_info[1] in ['23', '24', '25', '26', '27'] else f"芝/他({race_info[1]})"
                print(f"     {race_info[0]}m {track_type} 馬場:{race_info[2]}")
            print(f"     {chaku}着 ({ninki}番人気) 騎手:{jockey}")
            
            # ネット競馬と比較
            if i <= len(netkeiba_data):
                nk = netkeiba_data[i-1]
                print(f"     【ネット競馬】{nk[1]} {nk[3]} {nk[4]} {nk[5]} 騎手:{nk[6]}")
                if ba_name != nk[1]:
                    print(f"     ⚠️ 競馬場不一致！ PostgreSQL:{ba_name} vs ネット競馬:{nk[1]}")
        
        # 3. トラックコード分析
        print("\n【3. トラックコード分析】")
        cur.execute("""
            SELECT 
                ra.track_code,
                COUNT(*) as count
            FROM nvd_se se
            JOIN nvd_ra ra ON (
                se.kaisai_nen = ra.kaisai_nen
                AND se.kaisai_tsukihi = ra.kaisai_tsukihi
                AND se.keibajo_code = ra.keibajo_code
                AND se.race_bango = ra.race_bango
            )
            WHERE se.ketto_toroku_bango = %s
            GROUP BY ra.track_code
            ORDER BY count DESC
        """, (ketto_no,))
        
        track_stats = cur.fetchall()
        print("  トラックコード分布:")
        for code, count in track_stats:
            track_type = "ダート" if code in ['23', '24', '25', '26', '27'] else f"芝/他"
            print(f"    コード{code} ({track_type}): {count}レース")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_seasaw_game_2022()