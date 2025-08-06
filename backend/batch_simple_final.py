#!/usr/bin/env python3
"""
超シンプル版バッチ処理 - 問題を回避して確実に動作
"""
import sys
import os
import json
from datetime import datetime

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.mysql_connection_manager import get_mysql_manager

def simple_batch():
    """超シンプル版バッチ処理"""
    print("🚀 超シンプル版バッチ処理開始")
    print(f"🕐 開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # MySQL接続
    mysql_manager = get_mysql_manager()
    
    # 接続テスト
    print("📡 MySQL接続テスト...")
    if not mysql_manager.test_connection():
        print("❌ MySQL接続失敗")
        return
    print("✅ MySQL接続成功")
    
    # 出力ファイル
    output_file = f"data/simple_batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    # 新しいナレッジデータ
    knowledge = {
        "meta": {
            "created": datetime.now().isoformat(),
            "version": "simple_1.0"
        },
        "horses": {}
    }
    
    print("🐎 馬データ取得中...")
    try:
        # 超シンプルなクエリ
        horses = mysql_manager.execute_query("""
            SELECT DISTINCT BAMEI 
            FROM umagoto_race_joho 
            WHERE KAISAI_NEN = '2024'
            AND BAMEI IS NOT NULL 
            LIMIT 100
        """)
        
        print(f"✅ {len(horses)}頭を取得")
        
        processed = 0
        for horse_data in horses:
            horse_name = horse_data['BAMEI']
            
            # 各馬のレースデータ取得
            races = mysql_manager.execute_query("""
                SELECT KAKUTEI_CHAKUJUN, TANSHO_ODDS
                FROM umagoto_race_joho 
                WHERE BAMEI = %s 
                AND KAISAI_NEN = '2024'
                LIMIT 5
            """, (horse_name,))
            
            if races:
                knowledge["horses"][horse_name] = {
                    "name": horse_name,
                    "races": len(races),
                    "data": races[:3]  # 最初の3レースのみ
                }
                processed += 1
                
                if processed % 10 == 0:
                    print(f"⏳ {processed}頭処理完了")
        
        # 保存
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(knowledge, f, ensure_ascii=False, indent=2)
        
        print(f"\n🎉 処理完了!")
        print(f"📊 処理結果: {processed}頭")
        print(f"💾 保存先: {output_file}")
        
    except Exception as e:
        print(f"❌ エラー: {e}")

if __name__ == "__main__":
    simple_batch()