#!/usr/bin/env python3
"""
D-Logic生データナレッジ一括作成バッチ（最適化版）
クエリ最適化とバッチ処理効率化
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

def extract_horse_raw_data_optimized(horse_name: str) -> Dict[str, Any]:
    """最適化された生データ抽出"""
    
    # シンプルなクエリに変更（JOIN削除、必要最小限のフィールド）
    races = mysql_manager.execute_query("""
        SELECT 
            RACE_CODE,
            KAISAI_NEN,
            KAISAI_GAPPI,
            KAKUTEI_CHAKUJUN as finish,
            TANSHO_ODDS as odds,
            TANSHO_NINKIJUN as popularity,
            FUTAN_JURYO as weight,
            BATAIJU as horse_weight,
            ZOGEN_SA as weight_change,
            KISHUMEI_RYAKUSHO as jockey,
            CHOKYOSHIMEI_RYAKUSHO as trainer,
            SOHA_TIME as time,
            BAREI as age,
            SEIBETSU_CODE as sex
        FROM umagoto_race_joho 
        WHERE BAMEI = %s
        AND KAISAI_NEN IS NOT NULL
        AND KAKUTEI_CHAKUJUN IS NOT NULL
        ORDER BY KAISAI_NEN DESC, KAISAI_GAPPI DESC
        LIMIT 50
    """, (horse_name,))
    
    # 軽量データ処理
    race_history = []
    stats = {"total_races": 0, "wins": 0}
    
    for race in races:
        finish = None
        if race.get("finish") and str(race["finish"]).isdigit():
            finish = int(race["finish"])
        
        if finish:
            race_data = {
                "race_code": race.get("RACE_CODE"),
                "date": f"{race.get('KAISAI_NEN', '')}{race.get('KAISAI_GAPPI', '')}" if race.get('KAISAI_NEN') and race.get('KAISAI_GAPPI') else None,
                "finish": finish,
                "odds": float(race["odds"]) / 10 if race.get("odds") and str(race["odds"]).isdigit() else None,
                "popularity": int(race["popularity"]) if race.get("popularity") and str(race["popularity"]).isdigit() else None,
                "jockey": race.get("jockey"),
                "trainer": race.get("trainer")
            }
            
            race_history.append(race_data)
            stats["total_races"] += 1
            if finish == 1:
                stats["wins"] += 1
    
    # 基本情報
    basic_info = {}
    if race_history:
        latest = race_history[0]
        basic_info = {"last_race_date": latest.get("date")}
    
    return {
        "basic_info": basic_info,
        "race_history": race_history,
        "aggregated_stats": stats
    }

def batch_create_knowledge_optimized():
    """最適化バッチ処理"""
    start_time = time.time()
    print("🚀 D-Logic生データナレッジ一括作成開始（最適化版）")
    print(f"📅 対象期間: 2020年～2025年")
    print(f"🕐 開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 接続テスト
    if not mysql_manager.test_connection():
        print("❌ MySQL接続テスト失敗。処理を中止します。")
        return
    
    print("✅ MySQL接続テスト成功")
    manager = DLogicRawDataManager()
    current_count = len(manager.knowledge_data.get("horses", {}))
    print(f"📊 現在のナレッジ数: {current_count}頭")
    
    try:
        # 軽量クエリで対象馬を取得
        print("🔍 対象馬抽出中...")
        horses = mysql_manager.execute_query("""
            SELECT DISTINCT BAMEI, COUNT(*) as race_count
            FROM umagoto_race_joho 
            WHERE KAISAI_NEN >= '2020'
            AND BAMEI IS NOT NULL 
            AND BAMEI != ''
            AND KAKUTEI_CHAKUJUN IS NOT NULL
            GROUP BY BAMEI
            HAVING race_count >= 5
            ORDER BY race_count DESC
            LIMIT 5000
        """)
        
        total_horses = len(horses)
        print(f"🐎 対象馬数: {total_horses}頭")
        
        processed = 0
        errors = 0
        skipped = 0
        
        # 高速処理設定
        checkpoint_interval = 25
        save_interval = 100
        batch_delay = 1  # 1秒に短縮
        
        print(f"⚙️ 高速設定: チェックポイント{checkpoint_interval}, 保存{save_interval}, 遅延{batch_delay}秒")
        print("🏁 処理開始!")
        
        for i, horse in enumerate(horses):
            horse_name = horse['BAMEI']
            
            try:
                # 既存データスキップ
                if manager.get_horse_raw_data(horse_name):
                    skipped += 1
                    if skipped % 100 == 0:
                        print(f"⏭️  スキップ済み: {skipped}頭")
                    continue
                
                # 最適化されたデータ抽出
                start_extract = time.time()
                raw_data = extract_horse_raw_data_optimized(horse_name)
                extract_time = time.time() - start_extract
                
                if raw_data["race_history"]:
                    # ナレッジ追加
                    manager.add_horse_raw_data(horse_name, raw_data)
                    processed += 1
                    
                    # プログレス表示
                    if processed % checkpoint_interval == 0:
                        elapsed = time.time() - start_time
                        rate = processed / elapsed
                        remaining = total_horses - processed - skipped
                        eta = remaining / rate if rate > 0 else 0
                        current_time = datetime.now().strftime('%H:%M:%S')
                        
                        print(f"⏳ [{current_time}] {processed:4d}/{total_horses} 完了 "
                              f"速度:{rate:.1f}頭/秒 残り:{eta/60:.0f}分 "
                              f"抽出:{extract_time:.1f}s")
                    
                    # 定期保存
                    if processed % save_interval == 0:
                        manager._save_knowledge()
                        current_time = datetime.now().strftime('%H:%M:%S')
                        print(f"💾 [{current_time}] 中間保存完了: {processed}頭")
                
                # 高速処理用の短い待機
                if processed % 5 == 0:
                    time.sleep(batch_delay)
                        
            except Exception as e:
                errors += 1
                if errors <= 10:
                    print(f"❌ {horse_name} エラー: {e}")
                
                # エラー監視
                if errors % 50 == 0:
                    print(f"⚠️ エラー多発: {errors}件 - 接続確認中...")
                    mysql_manager.test_connection()
        
        # 最終保存
        manager._save_knowledge()
        
        elapsed_total = time.time() - start_time
        success_rate = (processed / total_horses * 100) if total_horses > 0 else 0
        
        print(f"\n✅ D-Logic生データナレッジ一括作成完了!")
        print(f"🕐 終了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📊 処理成功: {processed}頭 ({success_rate:.1f}%)")
        print(f"⏭️  スキップ: {skipped}頭")
        print(f"❌ エラー: {errors}頭")
        print(f"⏱️ 総処理時間: {elapsed_total/60:.1f}分")
        print(f"🚀 処理速度: {processed/(elapsed_total/60):.1f}頭/分")
        
        # ファイルサイズ確認
        if os.path.exists(manager.knowledge_file):
            file_size = os.path.getsize(manager.knowledge_file) / (1024 * 1024)
            print(f"📦 ファイルサイズ: {file_size:.1f}MB")
            new_total = len(manager.knowledge_data.get("horses", {}))
            print(f"📈 総ナレッジ数: {current_count} → {new_total}頭 (+{new_total-current_count})")
        
        # 簡易テスト
        print("\n🧪 簡易テスト...")
        test_horses = ["ドウデュース", "イクイノックス", "ジャックドール"]
        for horse in test_horses:
            if manager.get_horse_raw_data(horse):
                print(f"  ✅ {horse}: データ確認")
            else:
                print(f"  ⚠️ {horse}: データなし")
        
        # 最終レポート
        if success_rate > 80:
            print("\n🎉 バッチ処理大成功!")
        elif success_rate > 50:
            print("\n✅ バッチ処理成功!")
        else:
            print("\n⚠️ 処理率が低いです")
        
    except Exception as e:
        print(f"❌ バッチ処理エラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        mysql_manager.close_pool()
        print("🔌 MySQL接続プール終了")

if __name__ == "__main__":
    print("⚡ D-Logic生データナレッジ一括作成バッチ (最適化版)")
    print("🔧 最適化内容:")
    print("   - JOIN削除によるクエリ高速化")
    print("   - 軽量データ処理")
    print("   - 短い待機間隔")
    print("   - 頻繁な進捗表示")
    print("")
    batch_create_knowledge_optimized()