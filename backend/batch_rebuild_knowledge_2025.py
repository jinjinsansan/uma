#!/usr/bin/env python3
"""
D-Logic ナレッジファイル再構築バッチ 2025年版
2020-2025年の5走以上の馬データ（目標30,000頭）を効率的に再構築
"""
import os
import sys
import json
import time
import mysql.connector
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import defaultdict

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_mysql_connection():
    """MySQL接続を作成"""
    return mysql.connector.connect(
        host='172.25.160.1',
        port=3306,
        user='root',
        password='04050405Aoi-',
        database='mykeibadb',
        charset='utf8mb4',
        autocommit=True,
        buffered=True
    )

def extract_horse_raw_data(conn, horse_name: str) -> Dict[str, Any]:
    """単一馬の生データ抽出（5走以上）"""
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
            r.TRACK_CODE as track,
            r.BABA_JOTAI_CODE as ground_condition,
            r.TENKOU_CODE as weather
        FROM umagoto_race_joho u
        LEFT JOIN race_shosai r ON u.RACE_CODE = r.RACE_CODE
        WHERE u.BAMEI = %s
        AND u.KAISAI_NEN >= '2020'
        AND u.KAISAI_NEN <= '2025'
        AND u.KAKUTEI_CHAKUJUN IS NOT NULL
        ORDER BY u.KAISAI_NEN DESC, u.KAISAI_GAPPI DESC
    """, (horse_name,))
    
    races = cursor.fetchall()
    cursor.close()
    
    # 5走未満は除外
    if len(races) < 5:
        return {"race_history": []}
    
    # 生データ整形
    race_history = []
    aggregated_stats = {
        "total_races": 0,
        "wins": 0,
        "distance_performance": defaultdict(list),
        "jockey_performance": defaultdict(list),
        "trainer_performance": defaultdict(list),
        "track_performance": defaultdict(list),
        "ground_performance": defaultdict(list)
    }
    
    for race in races:
        # レース履歴データ
        race_data = {
            "race_code": race.get("RACE_CODE"),
            "date": f"{race.get('KAISAI_NEN', '')}/{race.get('KAISAI_GAPPI', '')[:2]}/{race.get('KAISAI_GAPPI', '')[2:4]}" if race.get('KAISAI_NEN') and race.get('KAISAI_GAPPI') else None,
            "finish": int(race["finish"]) if race.get("finish") and str(race["finish"]).isdigit() else None,
            "odds": float(race["odds"]) / 10 if race.get("odds") and str(race["odds"]).replace('.', '').isdigit() else None,
            "popularity": int(race["popularity"]) if race.get("popularity") and str(race["popularity"]).isdigit() else None,
            "weight": int(race["weight"]) if race.get("weight") and str(race["weight"]).isdigit() else None,
            "horse_weight": int(race["horse_weight"]) if race.get("horse_weight") and str(race["horse_weight"]).isdigit() else None,
            "weight_change": race.get("weight_change"),
            "jockey": race.get("jockey", "").strip() if race.get("jockey") else None,
            "trainer": race.get("trainer", "").strip() if race.get("trainer") else None,
            "corner_positions": [],
            "time": float(race["time"]) / 10 if race.get("time") and str(race["time"]).replace('.', '').isdigit() else None,
            "age": int(race["age"]) if race.get("age") and str(race["age"]).isdigit() else None,
            "sex": race.get("sex"),
            "distance": int(race["distance"]) if race.get("distance") and str(race["distance"]).isdigit() else None,
            "track": race.get("track"),
            "ground_condition": race.get("ground_condition"),
            "weather": race.get("weather")
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
            
            # 各種成績集計
            if race_data["distance"]:
                aggregated_stats["distance_performance"][str(race_data["distance"])].append(race_data["finish"])
            
            if race_data["jockey"]:
                aggregated_stats["jockey_performance"][race_data["jockey"]].append(race_data["finish"])
            
            if race_data["trainer"]:
                aggregated_stats["trainer_performance"][race_data["trainer"]].append(race_data["finish"])
            
            if race_data["track"]:
                aggregated_stats["track_performance"][race_data["track"]].append(race_data["finish"])
            
            if race_data["ground_condition"]:
                aggregated_stats["ground_performance"][race_data["ground_condition"]].append(race_data["finish"])
    
    # 基本情報（最新レースから）
    basic_info = {}
    if race_history:
        latest = race_history[0]
        basic_info = {
            "sex": latest.get("sex"),
            "age": latest.get("age"),
            "last_race_date": latest.get("date"),
            "main_trainer": max(aggregated_stats["trainer_performance"].items(), 
                              key=lambda x: len(x[1]))[0] if aggregated_stats["trainer_performance"] else None
        }
    
    # dict型をdictに変換
    aggregated_stats["distance_performance"] = dict(aggregated_stats["distance_performance"])
    aggregated_stats["jockey_performance"] = dict(aggregated_stats["jockey_performance"])
    aggregated_stats["trainer_performance"] = dict(aggregated_stats["trainer_performance"])
    aggregated_stats["track_performance"] = dict(aggregated_stats["track_performance"])
    aggregated_stats["ground_performance"] = dict(aggregated_stats["ground_performance"])
    
    return {
        "basic_info": basic_info,
        "race_history": race_history[:50],  # 最新50レースまで
        "aggregated_stats": aggregated_stats
    }

def rebuild_knowledge_2025():
    """2025年版ナレッジファイル再構築"""
    start_time = time.time()
    
    print("🏗️ D-Logic ナレッジファイル再構築開始（2025年版）")
    print(f"📅 対象期間: 2020年～2025年")
    print(f"🎯 対象条件: 5走以上の馬")
    print(f"🏁 目標: 30,000頭以上")
    print(f"🕐 開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # 出力ファイル
    output_file = "data/dlogic_raw_knowledge.json"
    temp_file = "data/dlogic_raw_knowledge_temp.json"
    
    # ナレッジ構造初期化
    knowledge = {
        "meta": {
            "created": datetime.now().isoformat(),
            "version": "2.0",
            "description": "D-Logic生データナレッジ 2020-2025年版",
            "criteria": "5走以上",
            "target_count": "30,000+",
            "last_updated": datetime.now().isoformat()
        },
        "horses": {}
    }
    
    conn = None
    total_processed = 0
    total_errors = 0
    
    try:
        # MySQL接続
        conn = create_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        
        print("📊 対象馬を抽出中...")
        
        # 5走以上の馬を効率的に取得（年度別集計を避ける）
        cursor.execute("""
            SELECT BAMEI, COUNT(*) as race_count
            FROM umagoto_race_joho
            WHERE KAISAI_NEN >= '2020'
            AND KAISAI_NEN <= '2025'
            AND BAMEI IS NOT NULL
            AND BAMEI != ''
            AND KAKUTEI_CHAKUJUN IS NOT NULL
            GROUP BY BAMEI
            HAVING race_count >= 5
            ORDER BY race_count DESC
            LIMIT 50000
        """)
        
        horses = cursor.fetchall()
        cursor.close()
        
        total_horses = len(horses)
        print(f"✅ 対象馬数: {total_horses:,}頭（5走以上）")
        
        if total_horses == 0:
            print("❌ 対象馬が見つかりません")
            return
        
        print("\n🏃 処理開始...")
        print("-"*60)
        
        # バッチ処理パラメータ
        checkpoint_interval = 100  # 進捗表示間隔
        save_interval = 500       # 保存間隔
        
        for idx, horse_data in enumerate(horses):
            horse_name = horse_data['BAMEI']
            race_count = horse_data['race_count']
            
            try:
                # 生データ抽出
                raw_data = extract_horse_raw_data(conn, horse_name)
                
                if raw_data["race_history"]:
                    # ナレッジに追加
                    knowledge["horses"][horse_name] = {
                        "name": horse_name,
                        "registered_race_count": race_count,
                        **raw_data
                    }
                    total_processed += 1
                    
                    # 進捗表示
                    if total_processed % checkpoint_interval == 0:
                        progress = (idx + 1) / total_horses * 100
                        elapsed = time.time() - start_time
                        rate = total_processed / elapsed if elapsed > 0 else 0
                        eta = (total_horses - idx - 1) / rate if rate > 0 else 0
                        
                        print(f"⏳ {total_processed:,}/{total_horses:,} 処理済 "
                              f"({progress:.1f}%) "
                              f"速度: {rate:.1f}頭/秒 "
                              f"残り: {eta/60:.1f}分")
                    
                    # 定期保存
                    if total_processed % save_interval == 0:
                        knowledge["meta"]["last_updated"] = datetime.now().isoformat()
                        knowledge["meta"]["current_count"] = total_processed
                        with open(temp_file, 'w', encoding='utf-8') as f:
                            json.dump(knowledge, f, ensure_ascii=False, indent=2)
                        print(f"💾 中間保存: {total_processed:,}頭完了")
                
            except Exception as e:
                total_errors += 1
                if total_errors <= 10:
                    print(f"❌ エラー {horse_name}: {str(e)}")
                
                # エラーが多すぎる場合は再接続
                if total_errors % 50 == 0:
                    print("⚠️ エラー多発、MySQL再接続...")
                    if conn:
                        conn.close()
                    conn = create_mysql_connection()
            
            # 30,000頭に達したら終了
            if total_processed >= 30000:
                print(f"\n✅ 目標の30,000頭に到達しました！")
                break
        
        # 最終保存
        knowledge["meta"]["last_updated"] = datetime.now().isoformat()
        knowledge["meta"]["total_count"] = total_processed
        knowledge["meta"]["status"] = "completed"
        
        print("\n💾 最終保存中...")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(knowledge, f, ensure_ascii=False, indent=2)
        
        # 一時ファイル削除
        if os.path.exists(temp_file):
            os.remove(temp_file)
        
        # 完了レポート
        elapsed_total = time.time() - start_time
        file_size = os.path.getsize(output_file) / (1024 * 1024) if os.path.exists(output_file) else 0
        
        print("\n" + "="*60)
        print("🎉 ナレッジファイル再構築完了！")
        print(f"📊 処理結果:")
        print(f"   - 処理成功: {total_processed:,}頭")
        print(f"   - エラー: {total_errors:,}件")
        print(f"   - 成功率: {(total_processed/len(horses)*100):.1f}%")
        print(f"   - 処理時間: {elapsed_total/3600:.1f}時間")
        print(f"   - 平均速度: {total_processed/(elapsed_total/60):.0f}頭/分")
        print(f"   - ファイルサイズ: {file_size:.1f}MB")
        print(f"   - 保存先: {os.path.abspath(output_file)}")
        print("="*60)
        
        # テスト実行
        print("\n🧪 動作確認テスト...")
        test_horses = ["ダノンザキッド", "ジャスティンミラノ", "シティオブトロイ", "レガレイラ", "ドウデュース"]
        
        for test_horse in test_horses:
            if test_horse in knowledge["horses"]:
                horse_data = knowledge["horses"][test_horse]
                race_count = len(horse_data.get("race_history", []))
                wins = horse_data.get("aggregated_stats", {}).get("wins", 0)
                print(f"  ✅ {test_horse}: {race_count}走 {wins}勝")
            else:
                print(f"  ⚠️ {test_horse}: データなし")
        
        print("\n✅ 再構築プロセス完了！")
        
    except Exception as e:
        print(f"\n❌ 致命的エラー: {e}")
        import traceback
        traceback.print_exc()
        
        # エラー時も途中経過を保存
        if knowledge["horses"]:
            knowledge["meta"]["status"] = "error"
            knowledge["meta"]["error"] = str(e)
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(knowledge, f, ensure_ascii=False, indent=2)
            print(f"💾 エラー保存: {temp_file}")
    
    finally:
        if conn:
            conn.close()
            print("🔌 MySQL接続終了")

if __name__ == "__main__":
    print("🚀 D-Logic ナレッジファイル再構築バッチ（2025年版）")
    print("")
    print("このバッチは以下の処理を行います：")
    print("  1. 2020-2025年のレースデータから5走以上の馬を抽出")
    print("  2. 各馬の詳細な生データを収集")
    print("  3. 30,000頭以上のデータをナレッジファイルに保存")
    print("")
    print("⚠️ 推定処理時間: 1-3時間")
    print("⚠️ 推定ファイルサイズ: 100MB以上")
    print("")
    print("続行しますか？ (yes/no): ", end="")
    
    response = input().strip().lower()
    if response in ['yes', 'y', 'はい']:
        print("\n🏁 バッチ処理を開始します！")
        rebuild_knowledge_2025()
    else:
        print("❌ バッチ処理をキャンセルしました")