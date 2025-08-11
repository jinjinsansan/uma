#!/usr/bin/env python3
"""
特定の馬をMySQLで高速検索
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
    print("MySQL馬名検索（高速版）")
    print("=" * 50)
    
    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        
        # 各馬を個別に検索
        horses = ['モズミコシ', 'バチェラーパーティ', 'シマエナガ']
        
        for horse in horses:
            print(f"\n【{horse}】")
            
            # 完全一致検索（高速）
            cursor.execute(
                "SELECT COUNT(*) FROM umagoto_race_joho WHERE BAMEI = %s",
                (horse,)
            )
            count = cursor.fetchone()[0]
            
            if count > 0:
                print(f"✅ 発見！ {count}レース")
                
                # 最初のレース情報を1件だけ取得
                cursor.execute(
                    "SELECT KAISAI_NEN, KAISAI_GAPPI FROM umagoto_race_joho WHERE BAMEI = %s LIMIT 1",
                    (horse,)
                )
                race = cursor.fetchone()
                if race:
                    print(f"   例: {race[0]}年{race[1]}")
            else:
                print("❌ 見つかりません")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"エラー: {e}")

if __name__ == "__main__":
    main()