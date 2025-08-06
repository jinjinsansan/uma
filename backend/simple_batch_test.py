#!/usr/bin/env python3
"""
シンプルバッチテスト - 問題箇所の特定
"""
import os
import sys
import time
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.mysql_connection_manager import get_mysql_manager

def simple_test():
    """シンプルテスト"""
    print("🔧 シンプルバッチテスト開始")
    
    mysql_manager = get_mysql_manager()
    
    print("1. 接続テスト...")
    if not mysql_manager.test_connection():
        print("❌ 接続失敗")
        return
    print("✅ 接続成功")
    
    print("2. 馬一覧取得テスト...")
    start = time.time()
    try:
        horses = mysql_manager.execute_query("""
            SELECT DISTINCT BAMEI 
            FROM umagoto_race_joho 
            WHERE KAISAI_NEN >= '2020'
            AND BAMEI IS NOT NULL 
            AND BAMEI != ''
            LIMIT 10
        """)
        elapsed = time.time() - start
        print(f"✅ {len(horses)}頭取得 ({elapsed:.1f}秒)")
        
        for horse in horses[:5]:
            print(f"   - {horse['BAMEI']}")
            
    except Exception as e:
        print(f"❌ エラー: {e}")
        return
    
    print("3. 単一馬レースデータ取得テスト...")
    if horses:
        test_horse = horses[0]['BAMEI']
        print(f"テスト馬: {test_horse}")
        
        start = time.time()
        try:
            races = mysql_manager.execute_query("""
                SELECT RACE_CODE, KAISAI_NEN, KAKUTEI_CHAKUJUN
                FROM umagoto_race_joho 
                WHERE BAMEI = %s
                AND KAISAI_NEN IS NOT NULL
                LIMIT 5
            """, (test_horse,))
            elapsed = time.time() - start
            print(f"✅ {len(races)}レース取得 ({elapsed:.1f}秒)")
            
        except Exception as e:
            print(f"❌ エラー: {e}")
    
    print("4. DLogicRawDataManager初期化テスト...")
    try:
        from services.dlogic_raw_data_manager import DLogicRawDataManager
        start = time.time()
        manager = DLogicRawDataManager()
        elapsed = time.time() - start
        print(f"✅ 初期化完了 ({elapsed:.1f}秒)")
        print(f"現在のナレッジ数: {len(manager.knowledge_data.get('horses', {}))}頭")
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()
    
    mysql_manager.close_pool()
    print("✅ テスト完了")

if __name__ == "__main__":
    simple_test()