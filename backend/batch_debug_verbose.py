#!/usr/bin/env python3
"""
デバッグ版バッチ処理 - 詳細ログ出力
"""
import os
import sys
import json
import time
from datetime import datetime
from typing import Dict, List, Any

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.mysql_connection_manager import get_mysql_manager
from services.dlogic_raw_data_manager import DLogicRawDataManager

# MySQL接続マネージャー
mysql_manager = get_mysql_manager()

def debug_batch_process():
    """デバッグ版バッチ処理"""
    print("🚀 デバッグ版バッチ処理開始")
    print(f"🕐 開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 接続テスト
    print("📡 MySQL接続テスト中...")
    if not mysql_manager.test_connection():
        print("❌ MySQL接続テスト失敗")
        return
    print("✅ MySQL接続テスト成功")
    
    # ナレッジマネージャー初期化
    print("📋 ナレッジマネージャー初期化中...")
    try:
        manager = DLogicRawDataManager()
        current_count = len(manager.knowledge_data.get("horses", {}))
        print(f"✅ 現在のナレッジ数: {current_count:,}頭")
    except Exception as e:
        print(f"❌ ナレッジマネージャー初期化エラー: {e}")
        return
    
    # 既存の馬名を取得
    print("🔍 既存データの解析中...")
    existing_horses = set(manager.knowledge_data.get("horses", {}).keys())
    print(f"📊 既存馬名数: {len(existing_horses):,}頭")
    
    # データベースから対象馬を抽出
    print("🐎 データベースから対象馬を抽出中...")
    try:
        horses = mysql_manager.execute_query("""
            SELECT DISTINCT BAMEI, COUNT(*) as race_count
            FROM umagoto_race_joho 
            WHERE KAISAI_NEN >= '2020'
            AND BAMEI IS NOT NULL 
            AND BAMEI != ''
            AND KAKUTEI_CHAKUJUN IS NOT NULL
            GROUP BY BAMEI
            HAVING race_count >= 3
            ORDER BY race_count DESC
            LIMIT 100
        """)
        print(f"✅ データベースから {len(horses):,}頭を抽出")
        
        # 未処理の馬のみフィルター
        unprocessed_horses = [h for h in horses if h['BAMEI'] not in existing_horses]
        print(f"🎯 未処理馬数: {len(unprocessed_horses):,}頭")
        
        if len(unprocessed_horses) == 0:
            print("✅ 全ての馬の処理が完了しています")
            
            # より多くの馬を対象にして再チェック
            print("🔍 対象範囲を拡大して再チェック...")
            horses_expanded = mysql_manager.execute_query("""
                SELECT DISTINCT BAMEI, COUNT(*) as race_count
                FROM umagoto_race_joho 
                WHERE KAISAI_NEN >= '2015'
                AND BAMEI IS NOT NULL 
                AND BAMEI != ''
                AND KAKUTEI_CHAKUJUN IS NOT NULL
                GROUP BY BAMEI
                HAVING race_count >= 2
                ORDER BY race_count DESC
                LIMIT 1000
            """)
            unprocessed_expanded = [h for h in horses_expanded if h['BAMEI'] not in existing_horses]
            print(f"📈 拡大範囲での未処理馬数: {len(unprocessed_expanded):,}頭")
            
            if len(unprocessed_expanded) > 0:
                print("🚀 拡大範囲で処理を継続します")
                unprocessed_horses = unprocessed_expanded[:500]  # 最大500頭まで
            else:
                print("✅ すべての処理が完了済みです")
                return
        
        # 実際の処理開始
        print(f"🏁 {len(unprocessed_horses):,}頭の処理を開始")
        processed = 0
        errors = 0
        
        for i, horse_data in enumerate(unprocessed_horses[:10]):  # 最初の10頭でテスト
            horse_name = horse_data['BAMEI']
            print(f"🐎 処理中: {horse_name} ({i+1}/{min(10, len(unprocessed_horses))})")
            
            try:
                # データ抽出
                raw_data = extract_horse_data_simple(horse_name)
                
                if raw_data:
                    manager.add_horse_knowledge(horse_name, raw_data)
                    processed += 1
                    print(f"✅ {horse_name} 処理完了")
                else:
                    print(f"⚠️ {horse_name} データなし")
                    
            except Exception as e:
                errors += 1
                print(f"❌ {horse_name} エラー: {e}")
        
        # 結果保存
        if processed > 0:
            manager.save_knowledge_data()
            print(f"💾 {processed}頭のデータを保存完了")
        
        print("\n📊 処理結果:")
        print(f"   処理成功: {processed}頭")
        print(f"   エラー: {errors}頭")
        
    except Exception as e:
        print(f"❌ データベースクエリエラー: {e}")

def extract_horse_data_simple(horse_name: str) -> Dict[str, Any]:
    """シンプルなデータ抽出"""
    try:
        races = mysql_manager.execute_query("""
            SELECT 
                KAKUTEI_CHAKUJUN as finish,
                TANSHO_ODDS as odds,
                TANSHO_NINKIJUN as popularity,
                KAISAI_NEN as year
            FROM umagoto_race_joho 
            WHERE BAMEI = %s
            AND KAISAI_NEN >= '2020'
            AND KAKUTEI_CHAKUJUN IS NOT NULL
            ORDER BY KAISAI_NEN DESC
            LIMIT 10
        """, (horse_name,))
        
        if not races:
            return None
        
        return {
            "basic_info": {
                "name": horse_name,
                "total_races": len(races),
                "recent_performance": races
            },
            "processed_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ {horse_name}のデータ抽出エラー: {e}")
        return None

if __name__ == "__main__":
    debug_batch_process()