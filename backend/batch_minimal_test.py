#!/usr/bin/env python3
"""
最小限テスト - 既存データ無視、2024年のみ、10頭限定
"""
import mysql.connector
import json
import time
from datetime import datetime

def minimal_test():
    """最小限テスト実行"""
    print("🚀 最小限テスト開始")
    start_time = time.time()
    
    # 出力ファイル
    output_file = f"data/minimal_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    # 直接MySQL接続
    print("📡 MySQL接続中...")
    conn = mysql.connector.connect(
        host='172.25.160.1',
        port=3306,
        user='root',
        password='04050405Aoi-',
        database='mykeibadb',
        charset='utf8mb4',
        autocommit=True,
        buffered=True
    )
    
    knowledge = {
        "meta": {
            "created": datetime.now().isoformat(),
            "version": "minimal_test",
            "target": "2024年のみ10頭"
        },
        "horses": {}
    }
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        print("🐎 2024年の馬名取得中...")
        # 超シンプルクエリ - 2024年のみ、10頭限定
        cursor.execute("""
            SELECT DISTINCT BAMEI
            FROM umagoto_race_joho 
            WHERE KAISAI_NEN = '2024'
            AND BAMEI IS NOT NULL 
            AND BAMEI <> ''
            LIMIT 10
        """)
        
        horses = cursor.fetchall()
        print(f"✅ {len(horses)}頭取得完了")
        
        processed = 0
        for horse_data in horses:
            horse_name = horse_data['BAMEI']
            print(f"🔍 処理中: {horse_name}")
            
            # 各馬の2024年レースデータのみ
            cursor.execute("""
                SELECT 
                    KAKUTEI_CHAKUJUN as finish,
                    TANSHO_ODDS as odds,
                    KAISAI_GAPPI as date
                FROM umagoto_race_joho 
                WHERE BAMEI = %s
                AND KAISAI_NEN = '2024'
                AND KAKUTEI_CHAKUJUN IS NOT NULL
                LIMIT 5
            """, (horse_name,))
            
            races = cursor.fetchall()
            
            if races:
                knowledge["horses"][horse_name] = {
                    "name": horse_name,
                    "races_2024": len(races),
                    "sample_races": races[:3]
                }
                processed += 1
                print(f"  ✅ {horse_name}: {len(races)}レース")
        
        # 保存
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(knowledge, f, ensure_ascii=False, indent=2)
        
        elapsed = time.time() - start_time
        print(f"\n🎉 テスト完了!")
        print(f"📊 結果: {processed}頭処理, {elapsed:.1f}秒")
        print(f"💾 保存先: {output_file}")
        
    except Exception as e:
        print(f"❌ エラー: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    minimal_test()