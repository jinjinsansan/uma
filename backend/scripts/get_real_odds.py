#!/usr/bin/env python3
"""
9/13阪神の実際のオッズデータを取得するスクリプト
"""

import psycopg2
import json

CONNECTION_PARAMS = {
    "host": "172.25.160.1",
    "port": "5432", 
    "database": "pckeiba",
    "user": "postgres",
    "password": "postgres"
}

def get_real_odds():
    """9/13阪神の実際のオッズを取得"""
    
    conn = psycopg2.connect(**CONNECTION_PARAMS)
    cur = conn.cursor()
    
    try:
        # jvd_o1テーブルから単勝・複勝オッズを取得
        print("=== 9/13阪神のオッズデータ取得 ===")
        
        # 日付の形式を確認（kaisai_nen=2025, kaisai_tsukihi=0913）
        cur.execute("""
            SELECT 
                race_bango,
                odds_tansho,
                odds_fukusho
            FROM jvd_o1
            WHERE kaisai_nen = '2025'
            AND kaisai_tsukihi = '0913'
            AND keibajo_code = '09'
            ORDER BY race_bango
        """)
        
        odds_data = cur.fetchall()
        
        if odds_data:
            print(f"オッズデータ件数: {len(odds_data)}")
            for race_no, tansho, fukusho in odds_data[:3]:
                print(f"  {race_no}R: 単勝オッズ長さ={len(tansho) if tansho else 0}, 複勝オッズ長さ={len(fukusho) if fukusho else 0}")
        else:
            print("jvd_o1にデータが見つかりません")
        
        # jvd_seテーブルからも確認
        print("\n=== jvd_seテーブルの実データ確認 ===")
        for race_no in [4, 7, 8, 9, 10, 11, 12]:
            cur.execute("""
                SELECT 
                    bamei,
                    tansho_odds,
                    tansho_ninkijun
                FROM jvd_se
                WHERE kaisai_date = '2025-09-13'
                AND jyocode = '09'
                AND race_number = %s
                ORDER BY umaban
            """, (race_no,))
            
            horses = cur.fetchall()
            if horses:
                print(f"\n{race_no}R（{len(horses)}頭）:")
                for i, (name, odds, ninki) in enumerate(horses[:3], 1):
                    print(f"  {i}番: {name.strip() if name else '?'} - オッズ={odds}, 人気={ninki}")
            else:
                print(f"\n{race_no}R: データなし")
        
        # jvd_o1のオッズデータ構造を詳しく確認
        print("\n=== jvd_o1テーブルの詳細確認 ===")
        cur.execute("""
            SELECT 
                race_bango,
                shusso_tosu,
                odds_tansho
            FROM jvd_o1
            WHERE kaisai_nen = '2025'
            AND kaisai_tsukihi = '0913'
            AND keibajo_code = '09'
            AND race_bango IN ('04', '07', '08', '09', '10', '11', '12')
            ORDER BY race_bango
        """)
        
        detailed_odds = cur.fetchall()
        for race_no, tosu, tansho_str in detailed_odds:
            if tansho_str:
                # オッズ文字列をパース（通常は固定長フォーマット）
                print(f"\n{race_no}R（出走{tosu}頭）の単勝オッズ:")
                # 各馬6桁（999.9形式）で格納されている可能性
                odds_len = len(tansho_str)
                odds_per_horse = 6  # 通常6桁
                num_horses = odds_len // odds_per_horse
                
                for i in range(min(5, num_horses)):  # 最初の5頭まで表示
                    start = i * odds_per_horse
                    end = start + odds_per_horse
                    odds_raw = tansho_str[start:end]
                    try:
                        odds_value = float(odds_raw) / 10.0
                        print(f"  {i+1}番馬: {odds_value}")
                    except:
                        print(f"  {i+1}番馬: パースエラー（{odds_raw}）")
                        
    except Exception as e:
        print(f"エラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    get_real_odds()