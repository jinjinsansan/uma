#!/usr/bin/env python3
"""正しいシーソーゲーム（2022年生）を探す"""

import psycopg2
import sys

CONNECTION_PARAMS = {
    "host": "172.25.160.1",
    "port": "5432",
    "database": "pckeiba",
    "user": "postgres",
    "password": "postgres"
}

def search_correct_seasaw_game():
    print("=" * 80)
    print("正しいシーソーゲームを検索（2022年生まれ）")
    print("=" * 80)
    
    try:
        conn = psycopg2.connect(**CONNECTION_PARAMS)
        cur = conn.cursor()
        
        # 1. 2022年生まれのシーソーゲームを検索
        print("\n【1. 2022年生まれのシーソーゲームを検索】")
        cur.execute("""
            SELECT 
                ketto_toroku_bango,
                bamei,
                seibetsu_code,
                seinengappi,
                ketto_joho_01b as sire,
                ketto_joho_02b as broodmare_sire
            FROM nvd_um
            WHERE bamei LIKE '%シーソーゲーム%'
                AND seinengappi LIKE '2022%'
        """)
        
        horses = cur.fetchall()
        print(f"  検索結果: {len(horses)}件")
        
        if horses:
            for horse in horses:
                print(f"\n  馬名: {horse[1].strip()}")
                print(f"  血統登録番号: {horse[0]}")
                print(f"  生年月日: {horse[3]}")
                print(f"  父: {horse[4]}")
                print(f"  母父: {horse[5]}")
        
        # 2. 最近のレースから逆引き検索
        print("\n【2. 2025年のレースから逆引き検索】")
        
        # 6月11日の大井11Rに出走した馬を検索
        print("\n  2025年6月11日 大井11R（東京ダービー）の出走馬:")
        cur.execute("""
            SELECT DISTINCT
                se.bamei,
                se.ketto_toroku_bango,
                se.kakutei_chakujun,
                se.kishumei_ryakusho
            FROM nvd_se se
            WHERE se.kaisai_nen = '2025'
                AND se.kaisai_tsukihi = '0611'
                AND se.keibajo_code = '42'
                AND se.race_bango = '11'
            ORDER BY se.kakutei_chakujun
            LIMIT 20
        """)
        
        horses_0611 = cur.fetchall()
        if horses_0611:
            for horse in horses_0611:
                print(f"    {horse[2]}着: {horse[0].strip()} ({horse[1]}) 騎手: {horse[3]}")
                if 'シーソー' in horse[0] or 'ゲーム' in horse[0]:
                    print(f"    ★ 該当馬発見！")
        else:
            print("    データなし")
        
        # 3. 船橋の6月11日も確認（CDNデータが船橋になっているため）
        print("\n  2025年6月11日 船橋11Rの出走馬:")
        cur.execute("""
            SELECT DISTINCT
                se.bamei,
                se.ketto_toroku_bango,
                se.kakutei_chakujun,
                se.kishumei_ryakusho
            FROM nvd_se se
            WHERE se.kaisai_nen = '2025'
                AND se.kaisai_tsukihi = '0611'
                AND se.keibajo_code = '44'
                AND se.race_bango = '11'
            ORDER BY se.kakutei_chakujun
            LIMIT 20
        """)
        
        horses_0611_f = cur.fetchall()
        if horses_0611_f:
            for horse in horses_0611_f:
                print(f"    {horse[2]}着: {horse[0].strip()} ({horse[1]}) 騎手: {horse[3]}")
                if 'シーソー' in horse[0] or 'ゲーム' in horse[0]:
                    print(f"    ★ 該当馬発見！")
        else:
            print("    データなし")
        
        # 4. 御神本訓騎手の騎乗馬を検索
        print("\n【3. 御神本訓騎手の2025年6月の騎乗馬】")
        cur.execute("""
            SELECT DISTINCT
                se.bamei,
                se.ketto_toroku_bango,
                se.kaisai_tsukihi,
                se.keibajo_code,
                se.race_bango,
                se.kakutei_chakujun
            FROM nvd_se se
            WHERE se.kaisai_nen = '2025'
                AND se.kaisai_tsukihi LIKE '06%'
                AND se.kishumei_ryakusho = '御神本訓'
            ORDER BY se.kaisai_tsukihi DESC
            LIMIT 10
        """)
        
        rides = cur.fetchall()
        if rides:
            for ride in rides:
                keibajo_map = {'42': '大井', '43': '川崎', '44': '船橋', '45': '浦和'}
                ba = keibajo_map.get(ride[3], ride[3])
                print(f"    {ride[2][:2]}/{ride[2][2:]} {ba} {ride[4]}R: {ride[0].strip()} ({ride[1]}) {ride[5]}着")
                if 'シーソー' in ride[0] or 'ゲーム' in ride[0]:
                    print(f"    ★ 該当馬発見！")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    search_correct_seasaw_game()