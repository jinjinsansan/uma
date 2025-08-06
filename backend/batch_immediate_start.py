#!/usr/bin/env python3
"""
即座開始用軽量バッチ処理
集計クエリを避けて効率的に処理
"""
import mysql.connector
import json
import time
import os
from datetime import datetime

def immediate_batch_start():
    """即座開始バッチ処理"""
    start_time = time.time()
    print("🚀 軽量バッチ処理即座開始")
    print(f"🎯 目標: 現役馬8,000頭の過去5走データ")
    print(f"🕐 開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 既存データ読み込み（軽量版）
    existing_horses = set()
    existing_file = "data/dlogic_raw_knowledge.json"
    if os.path.exists(existing_file):
        try:
            with open(existing_file, 'r', encoding='utf-8') as f:
                # 最初の1MBだけ読んで既存馬名抽出
                chunk = f.read(1024 * 1024)
                import re
                horse_names = re.findall(r'"([^"]+)": \{', chunk)
                existing_horses = set(horse_names)
                print(f"📊 既存馬名: {len(existing_horses)}頭（部分読み込み）")
        except:
            pass
    
    # 出力ファイル
    output_file = f"data/immediate_batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    # ナレッジ構造
    knowledge = {
        "meta": {
            "created": datetime.now().isoformat(),
            "version": "immediate_1.0",
            "target": "現役馬8000頭"
        },
        "horses": {}
    }
    
    # MySQL接続
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
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        total_processed = 0
        batch_size = 100
        
        # 年度別に効率的処理（集計クエリ回避）
        years = ['2025', '2024', '2023', '2022', '2021', '2020']
        
        for year in years:
            if total_processed >= 8000:
                break
                
            print(f"\n📅 {year}年処理開始")
            year_start = time.time()
            
            # 年度の馬を小バッチで取得（DISTINCT使用、COUNT回避）
            offset = 0
            year_processed = 0
            target_per_year = 1500
            
            while year_processed < target_per_year:
                # 小さなバッチで馬名取得
                cursor.execute("""
                    SELECT DISTINCT BAMEI
                    FROM umagoto_race_joho 
                    WHERE KAISAI_NEN = %s
                    AND BAMEI IS NOT NULL 
                    AND BAMEI <> ''
                    LIMIT %s OFFSET %s
                """, (year, batch_size, offset))
                
                horses = cursor.fetchall()
                if not horses:
                    break
                
                # 新規馬のみ処理
                for horse_data in horses:
                    horse_name = horse_data['BAMEI']
                    
                    if horse_name not in existing_horses:
                        # 馬の過去5走データ取得
                        cursor.execute("""
                            SELECT 
                                KAKUTEI_CHAKUJUN as finish,
                                TANSHO_ODDS as odds,
                                TANSHO_NINKIJUN as popularity,
                                KAISAI_NEN as year,
                                KAISAI_GAPPI as date
                            FROM umagoto_race_joho 
                            WHERE BAMEI = %s
                            AND KAISAI_NEN >= '2020'
                            ORDER BY KAISAI_NEN DESC, KAISAI_GAPPI DESC
                            LIMIT 5
                        """, (horse_name,))
                        
                        races = cursor.fetchall()
                        
                        if races:
                            knowledge["horses"][horse_name] = {
                                "name": horse_name,
                                "race_count": len(races),
                                "past_races": races,
                                "processed_at": datetime.now().isoformat()
                            }
                            
                            existing_horses.add(horse_name)
                            year_processed += 1
                            total_processed += 1
                            
                            if total_processed % 50 == 0:
                                elapsed = time.time() - start_time
                                speed = total_processed / elapsed if elapsed > 0 else 0
                                print(f"⏳ {total_processed:,}頭完了 (速度: {speed:.1f}頭/秒)")
                            
                            if total_processed % 200 == 0:
                                # 中間保存
                                save_knowledge(knowledge, output_file, total_processed)
                
                offset += batch_size
                
                if year_processed >= target_per_year:
                    break
            
            year_time = time.time() - year_start
            print(f"✅ {year}年完了: {year_processed}頭, {year_time/60:.1f}分")
        
        # 最終保存
        save_knowledge(knowledge, output_file, total_processed, final=True)
        
        total_time = time.time() - start_time
        print("\n" + "="*60)
        print("🎉 軽量バッチ処理完了!")
        print(f"📊 処理結果:")
        print(f"   - 新規追加: {total_processed:,}頭")
        print(f"   - 実行時間: {total_time/60:.1f}分")
        print(f"   - 処理速度: {total_processed/(total_time/60):.0f}頭/分")
        print(f"   - 出力ファイル: {output_file}")
        print("="*60)
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        save_knowledge(knowledge, output_file, total_processed, error=True)
    finally:
        cursor.close()
        conn.close()

def save_knowledge(knowledge, output_file, count, final=False, error=False):
    """進捗保存"""
    knowledge["meta"]["current_count"] = count
    knowledge["meta"]["last_save"] = datetime.now().isoformat()
    
    if final:
        knowledge["meta"]["status"] = "completed"
    elif error:
        knowledge["meta"]["status"] = "error"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(knowledge, f, ensure_ascii=False, indent=2)
    
    if not error:
        print(f"💾 保存: {count}頭")

if __name__ == "__main__":
    immediate_batch_start()