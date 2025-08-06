#!/usr/bin/env python3
"""
バッチ処理デバッグ版 - 問題箇所の特定
"""
import os
import sys
import time
from datetime import datetime

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.mysql_connection_manager import get_mysql_manager
from services.dlogic_raw_data_manager import DLogicRawDataManager

def debug_batch():
    """デバッグ用バッチ処理"""
    print("🔍 デバッグモード開始")
    print(f"🕐 開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Step 1: MySQL接続マネージャー初期化
    print("\n1. MySQL接続マネージャー初期化...")
    try:
        mysql_manager = get_mysql_manager()
        print("✅ MySQL接続マネージャー初期化成功")
    except Exception as e:
        print(f"❌ MySQL接続マネージャー初期化失敗: {e}")
        return
    
    # Step 2: 接続テスト
    print("\n2. MySQL接続テスト...")
    try:
        if mysql_manager.test_connection():
            print("✅ MySQL接続テスト成功")
        else:
            print("❌ MySQL接続テスト失敗")
            return
    except Exception as e:
        print(f"❌ MySQL接続テストエラー: {e}")
        return
    
    # Step 3: DLogicRawDataManager初期化
    print("\n3. DLogicRawDataManager初期化...")
    try:
        manager = DLogicRawDataManager()
        current_count = len(manager.knowledge_data.get("horses", {}))
        print(f"✅ DLogicRawDataManager初期化成功: {current_count}頭")
    except Exception as e:
        print(f"❌ DLogicRawDataManager初期化失敗: {e}")
        return
    
    # Step 4: クエリテスト（小規模）
    print("\n4. 小規模クエリテスト...")
    try:
        horses = mysql_manager.execute_query("""
            SELECT DISTINCT BAMEI, COUNT(*) as race_count
            FROM umagoto_race_joho 
            WHERE KAISAI_NEN >= '2020'
            AND BAMEI IS NOT NULL 
            AND BAMEI != ''
            GROUP BY BAMEI
            HAVING race_count >= 3
            ORDER BY race_count DESC
            LIMIT 5
        """)
        print(f"✅ クエリテスト成功: {len(horses)}頭取得")
        for horse in horses:
            print(f"   - {horse['BAMEI']}: {horse['race_count']}戦")
    except Exception as e:
        print(f"❌ クエリテストエラー: {e}")
        return
    
    # Step 5: 単一馬データ抽出テスト
    print("\n5. 単一馬データ抽出テスト...")
    if horses:
        test_horse = horses[0]['BAMEI']
        print(f"テスト対象馬: {test_horse}")
        
        try:
            start_time = time.time()
            races = mysql_manager.execute_query("""
                SELECT 
                    u.RACE_CODE,
                    u.KAISAI_NEN,
                    u.KAISAI_GAPPI,
                    u.KAKUTEI_CHAKUJUN as finish
                FROM umagoto_race_joho u
                WHERE u.BAMEI = %s
                AND u.KAISAI_NEN IS NOT NULL
                LIMIT 10
            """, (test_horse,))
            elapsed = time.time() - start_time
            print(f"✅ データ抽出成功: {len(races)}レース ({elapsed:.3f}秒)")
            
        except Exception as e:
            print(f"❌ データ抽出エラー: {e}")
            return
    
    # Step 6: 実際のバッチ処理（1頭のみ）
    print("\n6. 実バッチ処理テスト（1頭）...")
    if horses:
        test_horse = horses[0]['BAMEI']
        
        # 既存データ確認
        if manager.get_horse_raw_data(test_horse):
            print(f"⚠️ {test_horse}は既にデータが存在します")
        else:
            print(f"新規処理: {test_horse}")
            
            try:
                from batch_auto_start import extract_horse_raw_data
                
                start_time = time.time()
                raw_data = extract_horse_raw_data(test_horse)
                elapsed = time.time() - start_time
                
                if raw_data["race_history"]:
                    print(f"✅ データ抽出成功: {len(raw_data['race_history'])}レース ({elapsed:.3f}秒)")
                    
                    # ナレッジ追加テスト
                    manager.add_horse_raw_data(test_horse, raw_data)
                    print(f"✅ ナレッジ追加成功")
                else:
                    print(f"⚠️ レースデータなし")
                    
            except Exception as e:
                print(f"❌ バッチ処理エラー: {e}")
                import traceback
                traceback.print_exc()
                return
    
    print(f"\n🎉 デバッグテスト完了!")
    print(f"🕐 終了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 接続プール終了
    mysql_manager.close_pool()

if __name__ == "__main__":
    debug_batch()