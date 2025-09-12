#!/usr/bin/env python3
"""
9/13阪神の実際のオッズデータを正しいカラム名で取得
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
        # まずjvd_seテーブルのカラム名を確認
        print("=== jvd_seテーブルのカラム確認 ===")
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'jvd_se'
            AND column_name IN ('kaisai_nen', 'kaisai_tsukihi', 'keibajo_code', 'race_bango', 
                                'bamei', 'tansho_odds', 'tansho_ninkijun', 'jyocode', 'race_number')
            ORDER BY column_name
        """)
        columns = cur.fetchall()
        print("存在するカラム:")
        for col in columns:
            print(f"  {col[0]}")
        
        # jvd_seテーブルから9/13阪神のデータを取得（正しいカラム名で）
        print("\n=== jvd_seテーブルからデータ取得 ===")
        cur.execute("""
            SELECT 
                keibajo_code,
                race_bango,
                bamei,
                tansho_odds,
                tansho_ninkijun,
                umaban
            FROM jvd_se
            WHERE kaisai_nen = '2025'
            AND kaisai_tsukihi = '0913'
            AND keibajo_code = '09'
            AND race_bango IN ('04', '07', '08', '09', '10', '11', '12')
            ORDER BY race_bango, umaban
        """)
        
        horses = cur.fetchall()
        
        if horses:
            print(f"データ件数: {len(horses)}件")
            
            # レースごとにグループ化
            races = {}
            for keibajo, race_no, bamei, odds, ninki, umaban in horses:
                if race_no not in races:
                    races[race_no] = []
                races[race_no].append({
                    'umaban': umaban,
                    'bamei': bamei.strip() if bamei else '',
                    'odds': float(odds) if odds and odds != '0' else 0.0,
                    'ninki': int(ninki) if ninki else 0
                })
            
            # 各レースのデータを表示
            for race_no in sorted(races.keys()):
                horses_in_race = races[race_no]
                print(f"\n{int(race_no)}R（{len(horses_in_race)}頭）:")
                for h in horses_in_race[:5]:  # 最初の5頭まで表示
                    print(f"  {h['umaban']}番 {h['bamei']}: オッズ={h['odds']}, 人気={h['ninki']}")
            
            # データをJSONファイルに保存
            output_file = '/mnt/e/dev/Cusor/chatbot/uma/backend/scripts/odds_data_0913.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(races, f, ensure_ascii=False, indent=2)
            print(f"\n✅ オッズデータを保存: {output_file}")
            
        else:
            print("データが見つかりません")
            
            # デバッグ：全体のデータ件数を確認
            cur.execute("""
                SELECT COUNT(*) 
                FROM jvd_se
                WHERE kaisai_nen = '2025'
                AND kaisai_tsukihi = '0913'
            """)
            total = cur.fetchone()[0]
            print(f"9/13の全データ件数: {total}")
            
            # 競馬場コードの確認
            cur.execute("""
                SELECT DISTINCT keibajo_code 
                FROM jvd_se
                WHERE kaisai_nen = '2025'
                AND kaisai_tsukihi = '0913'
            """)
            keibajo_codes = cur.fetchall()
            print(f"9/13の競馬場コード: {[k[0] for k in keibajo_codes]}")
                        
    except Exception as e:
        print(f"エラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    get_real_odds()