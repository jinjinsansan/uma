#!/usr/bin/env python3
"""
欠けている馬をMySQLデータベースで直接確認するスクリプト（簡易版）
"""
import mysql.connector
from datetime import datetime

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

def main():
    print("=" * 80)
    print("MySQLデータベース 欠損馬調査（簡易版）")
    print("=" * 80)
    print(f"調査日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"データベース: mykeibadb")
    print()
    
    try:
        # MySQL接続
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        print("✅ MySQLに接続成功")
        print()
        
        # 各馬の調査（完全一致のみ）
        for horse_name in missing_horses:
            print(f"🐎 {horse_name} の調査")
            print("-" * 40)
            
            # 完全一致検索
            query = """
            SELECT COUNT(*) as count
            FROM umagoto_race_joho
            WHERE BAMEI = %s
            """
            
            cursor.execute(query, (horse_name,))
            result = cursor.fetchone()
            count = result[0] if result else 0
            
            if count > 0:
                print(f"✅ 完全一致で発見! レース数: {count}回")
                
                # 最初と最後のレース日を取得
                query2 = """
                SELECT MIN(KAISAI_NEN), MAX(KAISAI_NEN), MIN(KAISAI_GAPPI), MAX(KAISAI_GAPPI)
                FROM umagoto_race_joho
                WHERE BAMEI = %s
                """
                cursor.execute(query2, (horse_name,))
                dates = cursor.fetchone()
                if dates:
                    print(f"  - 活動期間: {dates[0]}年～{dates[1]}年")
                    print(f"  - 初戦: {dates[0]}{dates[2]}")
                    print(f"  - 最終戦: {dates[1]}{dates[3]}")
            else:
                print("❌ 完全一致なし")
                
                # 部分一致検索（簡易版）
                query3 = """
                SELECT DISTINCT BAMEI
                FROM umagoto_race_joho
                WHERE BAMEI LIKE %s
                LIMIT 5
                """
                cursor.execute(query3, (f"%{horse_name}%",))
                partial_matches = cursor.fetchall()
                
                if partial_matches:
                    print(f"\n部分一致で見つかった馬:")
                    for match in partial_matches:
                        print(f"  - {match[0]}")
            
            print()
        
        # 2015-2025年のデータ統計（簡易版）
        print("=" * 80)
        print("📊 年別データ統計")
        print("-" * 40)
        
        for year in range(2015, 2026):
            query = """
            SELECT COUNT(DISTINCT BAMEI) as unique_horses
            FROM umagoto_race_joho
            WHERE KAISAI_NEN = %s
            """
            cursor.execute(query, (str(year),))
            result = cursor.fetchone()
            if result and result[0] > 0:
                print(f"{year}年: {result[0]:,}頭")
        
        cursor.close()
        conn.close()
        print("\n✅ 調査完了")
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()