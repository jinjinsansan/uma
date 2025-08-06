#!/usr/bin/env python3
"""
D-Logic高速バッチ処理（残り作業専用）
既存のナレッジデータから未処理分のみを効率的に処理
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

def extract_horse_raw_data_fast(horse_name: str) -> Dict[str, Any]:
    """超高速データ抽出（最小限の情報のみ）"""
    
    races = mysql_manager.execute_query("""
        SELECT 
            KAKUTEI_CHAKUJUN as finish,
            TANSHO_ODDS as odds,
            TANSHO_NINKIJUN as popularity,
            SOHA_TIME as time,
            KAISAI_NEN as year
        FROM umagoto_race_joho 
        WHERE BAMEI = %s
        AND KAISAI_NEN >= '2020'
        AND KAKUTEI_CHAKUJUN IS NOT NULL
        ORDER BY KAISAI_NEN DESC
        LIMIT 20
    """, (horse_name,))
    
    if not races:
        return None
    
    # 基本統計のみ計算
    total_races = len(races)
    wins = sum(1 for race in races if race.get('finish') == 1)
    avg_odds = sum(float(race.get('odds', 0)) for race in races if race.get('odds')) / max(1, total_races)
    
    return {
        "basic_info": {
            "name": horse_name,
            "total_races": total_races,
            "wins": wins,
            "win_rate": round(wins / total_races * 100, 1) if total_races > 0 else 0,
            "avg_odds": round(avg_odds, 1)
        },
        "race_history": races[:10],  # 最新10レースのみ
        "processed_at": datetime.now().isoformat()
    }

def fast_batch_resume():
    """高速バッチ処理再開"""
    start_time = time.time()
    print("🚀 D-Logic高速バッチ処理開始")
    print(f"🕐 開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 接続テスト
    if not mysql_manager.test_connection():
        print("❌ MySQL接続テスト失敗")
        return
    
    print("✅ MySQL接続テスト成功")
    manager = DLogicRawDataManager()
    current_count = len(manager.knowledge_data.get("horses", {}))
    print(f"📊 現在のナレッジ数: {current_count:,}頭")
    
    # 既存の馬名を取得
    existing_horses = set(manager.knowledge_data.get("horses", {}).keys())
    print(f"📋 既存データ: {len(existing_horses):,}頭")
    
    try:
        # 小さなバッチで対象馬を取得（未処理分のみ）
        print("🔍 未処理馬の検索中...")
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
            LIMIT 2000
        """)
        
        # 未処理の馬のみフィルター
        unprocessed_horses = [h for h in horses if h['BAMEI'] not in existing_horses]
        total_unprocessed = len(unprocessed_horses)
        
        print(f"🐎 全対象馬数: {len(horses):,}頭")
        print(f"🎯 未処理馬数: {total_unprocessed:,}頭")
        
        if total_unprocessed == 0:
            print("✅ 全ての馬の処理が完了しています")
            return
        
        processed = 0
        errors = 0
        batch_size = 50
        
        for i, horse_data in enumerate(unprocessed_horses):
            horse_name = horse_data['BAMEI']
            
            try:
                # 高速データ抽出
                raw_data = extract_horse_raw_data_fast(horse_name)
                
                if raw_data:
                    manager.add_horse_knowledge(horse_name, raw_data)
                    processed += 1
                    
                    # 進行状況表示
                    if processed % 10 == 0:
                        elapsed = time.time() - start_time
                        speed = processed / elapsed if elapsed > 0 else 0
                        remaining = total_unprocessed - processed
                        eta = remaining / speed if speed > 0 else 0
                        
                        print(f"⏳ {processed:,}/{total_unprocessed:,} 完了 "
                              f"({processed/total_unprocessed*100:.1f}%) "
                              f"速度: {speed:.1f}頭/秒 "
                              f"残り時間: {eta/60:.1f}分")
                    
                    # バッチ保存
                    if processed % batch_size == 0:
                        manager.save_knowledge_data()
                        print(f"💾 中間保存: {processed:,}頭完了")
                        
                else:
                    errors += 1
                    
            except Exception as e:
                errors += 1
                if errors % 10 == 0:
                    print(f"⚠️ エラー累計: {errors}件")
        
        # 最終保存
        manager.save_knowledge_data()
        
        elapsed = time.time() - start_time
        final_count = len(manager.knowledge_data.get("horses", {}))
        
        print("\n" + "="*60)
        print("🎉 バッチ処理完了！")
        print(f"📊 最終結果:")
        print(f"   - 処理開始前: {current_count:,}頭")
        print(f"   - 新規追加: {processed:,}頭") 
        print(f"   - 最終総数: {final_count:,}頭")
        print(f"   - エラー数: {errors:,}件")
        print(f"   - 実行時間: {elapsed/60:.1f}分")
        print(f"   - 処理速度: {processed/(elapsed/60):.1f}頭/分")
        print("="*60)
        
    except Exception as e:
        print(f"❌ バッチ処理エラー: {str(e)}")
        # エラー時も保存
        manager.save_knowledge_data()
        
if __name__ == "__main__":
    fast_batch_resume()