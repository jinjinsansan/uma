#!/usr/bin/env python3
"""PostgreSQL（PC-KEIBA）から直接シーソーゲームのデータを取得して検証"""

import psycopg2
import sys
from datetime import datetime

# PostgreSQL接続情報
CONNECTION_PARAMS = {
    "host": "172.25.160.1",
    "port": "5432",
    "database": "pckeiba",
    "user": "postgres",
    "password": "postgres"
}

def investigate_seasaw_game():
    """シーソーゲームのデータをPostgreSQLから直接取得"""
    
    print("=" * 80)
    print("PostgreSQL直接調査：シーソーゲーム")
    print("=" * 80)
    
    try:
        # PostgreSQL接続
        print("\n📊 PostgreSQL接続中...")
        conn = psycopg2.connect(**CONNECTION_PARAMS)
        cur = conn.cursor()
        print("✅ 接続成功")
        
        # 1. シーソーゲームの馬情報を取得
        print("\n【1. 馬マスタ（nvd_um）からシーソーゲームを検索】")
        cur.execute("""
            SELECT 
                ketto_toroku_bango,
                bamei,
                seibetsu_code,
                seinengappi,
                ketto_joho_01b as sire,
                ketto_joho_02b as broodmare_sire
            FROM nvd_um
            WHERE bamei LIKE 'シーソーゲーム%'
        """)
        
        horses = cur.fetchall()
        print(f"  検索結果: {len(horses)}件")
        
        if not horses:
            print("  ❌ シーソーゲームが見つかりません")
            
            # 類似名を検索
            print("\n  類似名検索中...")
            cur.execute("""
                SELECT bamei, ketto_toroku_bango
                FROM nvd_um
                WHERE bamei LIKE '%シーソー%' OR bamei LIKE '%ゲーム%'
                LIMIT 10
            """)
            similar = cur.fetchall()
            if similar:
                print("  類似馬名:")
                for name, ketto in similar:
                    print(f"    - {name} ({ketto})")
            return
        
        # 馬情報を表示
        for horse in horses:
            ketto_no = horse[0]
            print(f"\n  馬名: {horse[1]}")
            print(f"  血統登録番号: {ketto_no}")
            print(f"  性別: {horse[2]}")
            print(f"  生年月日: {horse[3]}")
            print(f"  父: {horse[4]}")
            print(f"  母父: {horse[5]}")
        
        # 2. レース成績を取得
        print("\n【2. レース成績（nvd_se）から全レースを取得】")
        cur.execute("""
            SELECT 
                se.kaisai_nen,
                se.kaisai_tsukihi,
                se.keibajo_code,
                se.race_bango,
                se.umaban,
                se.wakuban,
                se.kakutei_chakujun,
                se.kishumei_ryakusho,
                se.futan_juryo,
                se.bataiju,
                se.zogen_fugo,
                se.zogen_sa,
                se.tansho_ninkijun,
                se.soha_time,
                se.kohan_3f,
                se.corner_1,
                se.corner_2, 
                se.corner_3,
                se.corner_4
            FROM nvd_se se
            WHERE se.ketto_toroku_bango = %s
            ORDER BY se.kaisai_nen DESC, se.kaisai_tsukihi DESC
        """, (ketto_no,))
        
        races = cur.fetchall()
        print(f"  総レース数: {len(races)}件")
        
        # 3. 各レースの詳細情報を取得
        print("\n【3. 各レースの詳細情報】")
        keibajo_map = {
            '42': '大井',
            '43': '川崎',
            '44': '船橋',
            '45': '浦和'
        }
        
        for i, race in enumerate(races, 1):
            kaisai_nen = race[0]
            kaisai_tsukihi = race[1]
            keibajo_code = race[2]
            race_bango = race[3]
            
            # レース情報を取得
            cur.execute("""
                SELECT 
                    kyori,
                    track_code,
                    babajotai_code_shiba,
                    babajotai_code_dirt,
                    tenko_code,
                    zenhan_3f
                FROM nvd_ra
                WHERE kaisai_nen = %s 
                    AND kaisai_tsukihi = %s
                    AND keibajo_code = %s
                    AND race_bango = %s
            """, (kaisai_nen, kaisai_tsukihi, keibajo_code, race_bango))
            
            race_info = cur.fetchone()
            
            print(f"\n  【レース{i}】{kaisai_nen}年{kaisai_tsukihi[:2]}月{kaisai_tsukihi[2:]}日")
            print(f"    競馬場コード: {keibajo_code} → {keibajo_map.get(keibajo_code, '不明')}")
            print(f"    レース番号: {race_bango}R")
            
            if race_info:
                print(f"    距離: {race_info[0]}m")
                print(f"    トラックコード: {race_info[1]}")
                print(f"    芝馬場状態: {race_info[2]}")
                print(f"    ダート馬場状態: {race_info[3]}")
                print(f"    天候: {race_info[4]}")
                print(f"    前半3F: {race_info[5]}")
            
            print(f"    着順: {race[6]}着")
            print(f"    騎手: {race[7]}")
            print(f"    負担重量: {race[8]}kg")
            print(f"    馬体重: {race[9]}kg ({race[10]}{race[11]})")
            print(f"    人気: {race[12]}番人気")
            print(f"    走破タイム: {race[13]}")
            print(f"    後半3F: {race[14]}")
            print(f"    通過順位: {race[15]}-{race[16]}-{race[17]}-{race[18]}")
            
            if i >= 7:  # 最初の7レースまで表示
                break
        
        # 4. ネット競馬の情報と比較
        print("\n【4. ネット競馬情報との照合】")
        print("  ネット競馬の情報:")
        netkeiba_data = [
            ("2025/06/11", "大井", "11R", "東京ダービー", "ダ2000", "3着"),
            ("2025/05/04", "盛岡", "12R", "ダイヤモンドC", "ダ1800", "1着"),
            ("2025/04/14", "大井", "7R", "クラシックチャレンジ", "ダ1800", "2着"),
            ("2025/03/28", "大井", "5R", "マトバダンス賞", "ダ1600", "1着"),
        ]
        
        print("\n  PostgreSQLデータ vs ネット競馬:")
        for i, (nk_date, nk_ba, nk_r, nk_name, nk_dist, nk_chaku) in enumerate(netkeiba_data, 1):
            print(f"\n  {i}. {nk_date} {nk_ba} {nk_r} {nk_name}")
            print(f"     ネット競馬: {nk_ba} {nk_dist} {nk_chaku}")
            
            if i <= len(races):
                race = races[i-1]
                pg_ba = keibajo_map.get(race[2], f"コード{race[2]}")
                print(f"     PostgreSQL: {pg_ba} (コード{race[2]}) {race[6]}着")
                
                if nk_ba != pg_ba:
                    print(f"     ⚠️ 競馬場不一致！")
        
        # 5. 競馬場コードの分布を確認
        print("\n【5. 競馬場コード分布】")
        cur.execute("""
            SELECT 
                keibajo_code,
                COUNT(*) as count
            FROM nvd_se
            WHERE ketto_toroku_bango = %s
            GROUP BY keibajo_code
            ORDER BY count DESC
        """, (ketto_no,))
        
        distribution = cur.fetchall()
        for code, count in distribution:
            ba_name = keibajo_map.get(code, f"不明({code})")
            print(f"  {ba_name}: {count}レース")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    investigate_seasaw_game()