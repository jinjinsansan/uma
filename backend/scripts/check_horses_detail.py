#!/usr/bin/env python3
"""
発見した馬の詳細情報を取得
"""
import mysql.connector

# MySQL接続設定
config = {
    'user': 'root',
    'password': '04050405Aoi-',
    'host': '172.25.160.1',
    'database': 'mykeibadb',
    'port': 3306
}

def main():
    print("発見した馬の詳細調査")
    print("=" * 50)
    
    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        
        horses = ['モズミコシ', 'バチェラーパーティ', 'シマエナガ']
        
        for horse in horses:
            print(f"\n【{horse}】の全レース情報")
            print("-" * 40)
            
            # 全レース情報を取得
            cursor.execute("""
                SELECT 
                    KAISAI_NEN,
                    KAISAI_GAPPI,
                    KEIBAJO_CODE,
                    RACE_BANGO,
                    UMABAN,
                    KAKUTEI_CHAKUJUN,
                    SOHA_TIME
                FROM umagoto_race_joho 
                WHERE BAMEI = %s
                ORDER BY KAISAI_NEN, KAISAI_GAPPI
            """, (horse,))
            
            races = cursor.fetchall()
            
            print(f"総レース数: {len(races)}回")
            
            for i, race in enumerate(races, 1):
                year, date, track, race_no, uma_no, rank, time = race
                print(f"{i}. {year}年{date} {track}競馬場 {race_no}R {uma_no}番 着順:{rank} タイム:{time}")
        
        # なぜナレッジに含まれないか調査
        print("\n\n【ナレッジ収録条件の確認】")
        print("ナレッジ収録条件: 2015-2025年、5走以上")
        print("-" * 40)
        
        for horse in horses:
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_races,
                    MIN(KAISAI_NEN) as first_year,
                    MAX(KAISAI_NEN) as last_year
                FROM umagoto_race_joho 
                WHERE BAMEI = %s
            """, (horse,))
            
            result = cursor.fetchone()
            total, first_year, last_year = result
            
            print(f"\n{horse}:")
            print(f"  レース数: {total}回")
            print(f"  活動期間: {first_year}年～{last_year}年")
            
            # 2015年以降のレース数
            cursor.execute("""
                SELECT COUNT(*)
                FROM umagoto_race_joho 
                WHERE BAMEI = %s AND KAISAI_NEN >= '2015'
            """, (horse,))
            
            recent_count = cursor.fetchone()[0]
            print(f"  2015年以降: {recent_count}回")
            
            if recent_count < 5:
                print(f"  → ❌ 5走未満のためナレッジ対象外")
            else:
                print(f"  → ⚠️ 条件を満たすが何らかの理由で未収録")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"エラー: {e}")

if __name__ == "__main__":
    main()