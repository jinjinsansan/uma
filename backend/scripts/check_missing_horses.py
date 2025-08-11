#!/usr/bin/env python3
"""
欠けている馬をMySQLデータベースで直接確認するスクリプト
"""
import mysql.connector
from datetime import datetime
import json

# MySQL接続設定
config = {
    'user': 'root',
    'password': '04050405Aoi-',
    'host': '172.25.160.1',
    'database': 'mykeibadb',
    'port': 3306
}

# 調査対象の馬
missing_horses = [
    'モズミコシ',
    'バチェラーパーティ',
    'シマエナガ'
]

def search_horse_in_mysql(conn, horse_name):
    """MySQLデータベースで馬を検索"""
    cursor = conn.cursor(dictionary=True)
    
    # 完全一致検索
    query = """
    SELECT DISTINCT 
        BAMEI,
        COUNT(*) as race_count,
        MIN(KAISAI_NEN) as first_year,
        MAX(KAISAI_NEN) as last_year,
        MIN(KAISAI_GAPPI) as first_date,
        MAX(KAISAI_GAPPI) as last_date
    FROM umagoto_race_joho
    WHERE BAMEI = %s
    GROUP BY BAMEI
    """
    
    cursor.execute(query, (horse_name,))
    exact_results = cursor.fetchall()
    
    # 部分一致検索（前方一致、後方一致、部分一致）
    partial_queries = [
        ("前方一致", f"{horse_name}%"),
        ("後方一致", f"%{horse_name}"),
        ("部分一致", f"%{horse_name}%")
    ]
    
    partial_results = {}
    for match_type, pattern in partial_queries:
        query = """
        SELECT DISTINCT BAMEI
        FROM umagoto_race_joho
        WHERE BAMEI LIKE %s
        LIMIT 10
        """
        cursor.execute(query, (pattern,))
        partial_results[match_type] = cursor.fetchall()
    
    cursor.close()
    return exact_results, partial_results

def check_race_years(conn, start_year, end_year):
    """指定期間のレース件数を確認"""
    cursor = conn.cursor(dictionary=True)
    
    query = """
    SELECT 
        KAISAI_NEN as year,
        COUNT(DISTINCT BAMEI) as unique_horses,
        COUNT(*) as total_records
    FROM umagoto_race_joho
    WHERE KAISAI_NEN BETWEEN %s AND %s
    GROUP BY KAISAI_NEN
    ORDER BY KAISAI_NEN
    """
    
    cursor.execute(query, (start_year, end_year))
    results = cursor.fetchall()
    cursor.close()
    return results

def main():
    print("=" * 80)
    print("MySQLデータベース 欠損馬調査")
    print("=" * 80)
    print(f"調査日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"データベース: keiba_dw")
    print()
    
    try:
        # MySQL接続
        conn = mysql.connector.connect(**config)
        print("✅ MySQLに接続成功")
        print()
        
        # 各馬の調査
        for horse_name in missing_horses:
            print(f"🐎 {horse_name} の調査")
            print("-" * 40)
            
            exact_results, partial_results = search_horse_in_mysql(conn, horse_name)
            
            if exact_results:
                print("✅ 完全一致で発見!")
                for result in exact_results:
                    print(f"  - レース数: {result['race_count']}回")
                    print(f"  - 活動期間: {result['first_year']}年～{result['last_year']}年")
                    print(f"  - 初戦: {result['first_date']}")
                    print(f"  - 最終戦: {result['last_date']}")
            else:
                print("❌ 完全一致なし")
            
            # 部分一致結果
            for match_type, results in partial_results.items():
                if results and len(results) > 0:
                    print(f"\n{match_type}で見つかった馬:")
                    for r in results[:5]:  # 最大5件表示
                        print(f"  - {r['BAMEI']}")
            
            print()
        
        # 2015-2025年のデータ概要
        print("=" * 80)
        print("📊 2015-2025年のデータ概要")
        print("-" * 40)
        
        year_stats = check_race_years(conn, 2015, 2025)
        total_horses = 0
        total_records = 0
        
        for stat in year_stats:
            print(f"{stat['year']}年: {stat['unique_horses']:,}頭 ({stat['total_records']:,}レコード)")
            total_horses += stat['unique_horses']
            total_records += stat['total_records']
        
        print("-" * 40)
        print(f"合計: 約{total_horses:,}頭（延べ）, {total_records:,}レコード")
        
        # 最新のレース日を確認
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(KAISAI_GAPPI) as latest_date FROM RACE_RESULT")
        latest_date = cursor.fetchone()[0]
        print(f"\n最新レース日: {latest_date}")
        cursor.close()
        
        conn.close()
        print("\n✅ 調査完了")
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()