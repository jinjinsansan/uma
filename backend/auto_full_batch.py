#!/usr/bin/env python3
"""
D-Logic生データナレッジ一括作成バッチ（自動実行版）
2020-2025年の全競走馬の生データを抽出・保存
"""
import mysql.connector
import json
import os
from datetime import datetime
from typing import Dict, List, Any
from services.dlogic_raw_data_manager import DLogicRawDataManager
import time

def get_mysql_connection():
    """MySQL接続取得"""
    return mysql.connector.connect(
        host='172.25.160.1',
        port=3306,
        user='root',
        password='04050405Aoi-',
        database='mykeibadb',
        charset='utf8mb4'
    )

def extract_horse_raw_data(conn, horse_name: str) -> Dict[str, Any]:
    """単一馬の生データ抽出"""
    cursor = conn.cursor(dictionary=True)
    
    # レース履歴取得
    cursor.execute("""
        SELECT 
            u.RACE_CODE,
            u.KAISAI_NEN,
            u.KAISAI_GAPPI,
            u.KAKUTEI_CHAKUJUN as finish,
            u.TANSHO_ODDS as odds,
            u.TANSHO_NINKIJUN as popularity,
            u.FUTAN_JURYO as weight,
            u.BATAIJU as horse_weight,
            u.ZOGEN_SA as weight_change,
            u.KISHUMEI_RYAKUSHO as jockey,
            u.CHOKYOSHIMEI_RYAKUSHO as trainer,
            u.CORNER1_JUNI,
            u.CORNER2_JUNI,
            u.CORNER3_JUNI,
            u.CORNER4_JUNI,
            u.SOHA_TIME as time,
            u.BAREI as age,
            u.SEIBETSU_CODE as sex,
            r.KYORI as distance,
            r.TRACK_CODE as track
        FROM umagoto_race_joho u
        LEFT JOIN race_shosai r ON u.RACE_CODE = r.RACE_CODE
        WHERE u.BAMEI = %s
        AND u.KAISAI_NEN IS NOT NULL
        ORDER BY u.KAISAI_NEN DESC, u.KAISAI_GAPPI DESC
    """, (horse_name,))
    
    races = cursor.fetchall()
    
    # 生データ整形
    race_history = []
    aggregated_stats = {
        "total_races": 0,
        "wins": 0,
        "distance_performance": {},
        "jockey_performance": {},
        "trainer_performance": {}
    }
    
    for race in races:
        # レース履歴データ
        race_data = {
            "race_code": race.get("RACE_CODE"),
            "date": f"{race.get('KAISAI_NEN', '')}{race.get('KAISAI_GAPPI', '')}" if race.get('KAISAI_NEN') and race.get('KAISAI_GAPPI') else None,
            "finish": int(race["finish"]) if race.get("finish") and str(race["finish"]).isdigit() else None,
            "odds": float(race["odds"]) / 10 if race.get("odds") and str(race["odds"]).isdigit() else None,
            "popularity": int(race["popularity"]) if race.get("popularity") and str(race["popularity"]).isdigit() else None,
            "weight": int(race["weight"]) if race.get("weight") and str(race["weight"]).isdigit() else None,
            "horse_weight": int(race["horse_weight"]) if race.get("horse_weight") and str(race["horse_weight"]).isdigit() else None,
            "weight_change": race.get("weight_change"),
            "jockey": race.get("jockey"),
            "trainer": race.get("trainer"),
            "corner_positions": [],
            "time": float(race["time"]) / 10 if race.get("time") and str(race["time"]).isdigit() else None,
            "age": int(race["age"]) if race.get("age") and str(race["age"]).isdigit() else None,
            "sex": race.get("sex"),
            "distance": int(race["distance"]) if race.get("distance") and str(race["distance"]).isdigit() else None,
            "track": race.get("track")
        }
        
        # コーナー順位
        for i in range(1, 5):
            corner = race.get(f"CORNER{i}_JUNI")
            if corner and str(corner).isdigit():
                race_data["corner_positions"].append(int(corner))
        
        if race_data["finish"]:
            race_history.append(race_data)
            
            # 集計データ更新
            aggregated_stats["total_races"] += 1
            if race_data["finish"] == 1:
                aggregated_stats["wins"] += 1
            
            # 距離別成績
            if race_data["distance"]:
                dist_key = str(race_data["distance"])
                if dist_key not in aggregated_stats["distance_performance"]:
                    aggregated_stats["distance_performance"][dist_key] = []
                aggregated_stats["distance_performance"][dist_key].append(race_data["finish"])
            
            # 騎手別成績
            if race_data["jockey"]:
                if race_data["jockey"] not in aggregated_stats["jockey_performance"]:
                    aggregated_stats["jockey_performance"][race_data["jockey"]] = []
                aggregated_stats["jockey_performance"][race_data["jockey"]].append(race_data["finish"])
            
            # 調教師別成績
            if race_data["trainer"]:
                if race_data["trainer"] not in aggregated_stats["trainer_performance"]:
                    aggregated_stats["trainer_performance"][race_data["trainer"]] = []
                aggregated_stats["trainer_performance"][race_data["trainer"]].append(race_data["finish"])
    
    cursor.close()
    
    # 基本情報（最新レースから）
    basic_info = {}
    if race_history:
        latest = race_history[0]
        basic_info = {
            "sex": latest.get("sex"),
            "age": latest.get("age"),
            "last_race_date": latest.get("date")
        }
    
    return {
        "basic_info": basic_info,
        "race_history": race_history[:50],  # 最新50レースまで
        "aggregated_stats": aggregated_stats
    }

def auto_batch_create_knowledge():
    """自動バッチ処理メイン"""
    import sys
    sys.stdout.reconfigure(line_buffering=True)  # 行バッファリング有効化
    
    start_time = time.time()
    print("🏗️ D-Logic生データナレッジ一括作成開始（自動実行）")
    print(f"📅 対象期間: 2020年～2025年")
    print(f"🎯 目標: 10,000頭のナレッジ作成")
    print(f"⏱️ 推定時間: 約8時間")
    print("=" * 60)
    sys.stdout.flush()
    
    manager = DLogicRawDataManager()
    
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 2020年以降の馬を取得（レース数3以上）
        print("🔍 対象馬抽出中...")
        cursor.execute("""
            SELECT DISTINCT BAMEI, COUNT(*) as race_count
            FROM umagoto_race_joho 
            WHERE KAISAI_NEN >= '2020'
            AND BAMEI IS NOT NULL 
            AND BAMEI <> ''
            GROUP BY BAMEI
            HAVING race_count >= 3
            ORDER BY race_count DESC
            LIMIT 10000
        """)
        
        horses = cursor.fetchall()
        total_horses = len(horses)
        print(f"🐎 対象馬数: {total_horses}頭")
        
        processed = 0
        errors = 0
        start_processing_time = time.time()
        
        # プログレス表示用
        checkpoint_interval = 100
        save_interval = 500
        
        for horse in horses:
            horse_name = horse['BAMEI']
            
            try:
                # 既に登録済みの場合はスキップ
                if manager.get_horse_raw_data(horse_name):
                    continue
                
                # 生データ抽出
                raw_data = extract_horse_raw_data(conn, horse_name)
                
                if raw_data["race_history"]:
                    # ナレッジに追加
                    manager.add_horse_raw_data(horse_name, raw_data)
                    processed += 1
                    
                    # プログレス表示
                    if processed % checkpoint_interval == 0:
                        elapsed = time.time() - start_processing_time
                        rate = processed / elapsed
                        eta = (total_horses - processed) / rate if rate > 0 else 0
                        print(f"⏳ {processed:5d}/{total_horses} 処理完了 "
                              f"(速度: {rate:.1f}頭/秒, 残り時間: {eta/3600:.1f}時間)")
                        # 強制フラッシュ
                        import sys
                        sys.stdout.flush()
                    
                    # 定期保存
                    if processed % save_interval == 0:
                        manager._save_knowledge()
                        print(f"💾 中間保存: {processed}頭完了")
                        
            except Exception as e:
                errors += 1
                if errors <= 10:
                    print(f"❌ {horse_name} エラー: {e}")
        
        # 最終保存
        manager._save_knowledge()
        
        elapsed_total = time.time() - start_time
        print(f"\n✅ D-Logic生データナレッジ一括作成完了!")
        print(f"📊 処理成功: {processed}頭")
        print(f"❌ エラー: {errors}頭")
        print(f"⏱️ 処理時間: {elapsed_total/3600:.1f}時間")
        print(f"📁 保存先: {manager.knowledge_file}")
        
        # 性能テスト
        print("\n🧪 性能テスト実行...")
        from services.fast_dlogic_engine import FastDLogicEngine
        engine = FastDLogicEngine()
        
        test_horses = [h['BAMEI'] for h in horses[:5]]
        calc_start = time.time()
        
        for horse_name in test_horses:
            result = engine.analyze_single_horse(horse_name)
            calc_time = result.get('calculation_time_seconds', 0)
            score = result.get('total_score', 0)
            source = result.get('data_source', 'unknown')
            
            print(f"  🐎 {horse_name:15s} {score:6.1f}点 "
                  f"({calc_time:.3f}秒) - {source}")
        
        calc_total = time.time() - calc_start
        avg_calc_time = calc_total / 5
        print(f"  📊 平均計算時間: {avg_calc_time:.3f}秒/頭")
        
        if avg_calc_time <= 0.1:
            print(f"  🎯 性能目標達成: EXCELLENT（目標0.1秒 vs 実測{avg_calc_time:.3f}秒）")
        else:
            print(f"  🟡 要改善: 目標0.1秒 vs 実測{avg_calc_time:.3f}秒")
        
        return {
            "success": True,
            "processed_horses": processed,
            "errors": errors,
            "total_time_hours": elapsed_total / 3600,
            "avg_calc_time": avg_calc_time
        }
        
    except Exception as e:
        print(f"❌ バッチ処理エラー: {e}")
        return {"success": False, "error": str(e)}
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("🚀 D-Logic 10,000頭フルバッチ処理（自動実行）")
    print("📋 処理内容:")
    print("  - 2020-2025年の10,000頭のデータ抽出")
    print("  - 生データナレッジ作成")
    print("  - 高速D-Logic計算システム構築")
    print("  - 推定処理時間: 約8時間")
    print("\n🔄 自動実行開始...")
    
    result = auto_batch_create_knowledge()
    
    if result["success"]:
        print(f"\n🎉 フルバッチ処理成功!")
        print(f"📊 処理統計:")
        print(f"  - 成功: {result['processed_horses']}頭")
        print(f"  - エラー: {result['errors']}頭")
        print(f"  - 処理時間: {result['total_time_hours']:.1f}時間")
        print(f"  - 平均計算速度: {result['avg_calc_time']:.3f}秒/頭")
        print(f"\n✅ D-Logicナレッジファイルシステム完成!")
    else:
        print(f"❌ フルバッチ処理失敗: {result.get('error')}")