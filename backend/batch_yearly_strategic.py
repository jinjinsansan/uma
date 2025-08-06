#!/usr/bin/env python3
"""
年度別戦略的バッチ処理
現役馬8,000頭の過去5走データを1週間で完成
"""
import mysql.connector
import json
import time
import os
from datetime import datetime
from collections import defaultdict

def yearly_strategic_batch():
    """年度別戦略的バッチ処理"""
    start_time = time.time()
    print("🚀 年度別戦略的バッチ処理開始")
    print(f"🎯 目標: 現役馬8,000頭の過去5走データ")
    print(f"⏰ 期限: 1週間以内")
    print(f"🕐 開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 既存データ効率的読み込み
    existing_horses = load_existing_horses_minimal()
    print(f"📊 既存データ: {len(existing_horses):,}頭")
    
    # 出力ファイル
    output_file = f"data/yearly_batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    # 新しいナレッジ構造
    new_knowledge = {
        "meta": {
            "created": datetime.now().isoformat(),
            "version": "yearly_strategic_1.0",
            "target": "現役馬8000頭",
            "years": "2020-2025"
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
    
    try:
        total_processed = 0
        target_per_year = 1500  # 年あたり1500頭目標
        
        # 年度別処理（最新年度から）
        years = ['2025', '2024', '2023', '2022', '2021', '2020']
        
        for year in years:
            if total_processed >= 8000:  # 目標達成で終了
                break
                
            print(f"\n📅 {year}年処理開始")
            year_start = time.time()
            
            # その年の馬名を効率的取得
            year_horses = get_year_horses_fast(conn, year, existing_horses, target_per_year)
            print(f"   🐎 {year}年新規馬: {len(year_horses)}頭発見")
            
            if not year_horses:
                print(f"   ⏭️ {year}年: 新規馬なし、スキップ")
                continue
            
            # 馬データ処理
            year_processed = 0
            for horse_name in year_horses:
                horse_data = extract_horse_past_5_races(conn, horse_name)
                
                if horse_data:
                    new_knowledge["horses"][horse_name] = horse_data
                    existing_horses.add(horse_name)  # 重複回避リストに追加
                    year_processed += 1
                    total_processed += 1
                    
                    # 進行状況表示
                    if year_processed % 50 == 0:
                        elapsed = time.time() - year_start
                        speed = year_processed / elapsed if elapsed > 0 else 0
                        print(f"   📈 {year}年: {year_processed}頭完了 ({speed:.1f}頭/秒)")
                    
                    # 中間保存
                    if total_processed % 200 == 0:
                        save_progress(new_knowledge, output_file, total_processed)
                
                # 年あたりの上限チェック
                if year_processed >= target_per_year:
                    break
            
            year_time = time.time() - year_start
            print(f"   ✅ {year}年完了: {year_processed}頭, {year_time/60:.1f}分")
            print(f"   📊 累計: {total_processed:,}頭")
            
            # 目標達成チェック
            if total_processed >= 8000:
                print(f"🎯 目標達成! {total_processed:,}頭処理完了")
                break
        
        # 最終保存
        finalize_knowledge(new_knowledge, output_file, total_processed)
        
        total_time = time.time() - start_time
        print("\n" + "="*70)
        print("🎉 年度別戦略的バッチ処理完了!")
        print(f"📊 最終結果:")
        print(f"   - 新規追加馬: {total_processed:,}頭")
        print(f"   - 既存込み総数: {len(existing_horses) + total_processed:,}頭") 
        print(f"   - 実行時間: {total_time/3600:.1f}時間")
        print(f"   - 処理速度: {total_processed/(total_time/3600):.0f}頭/時間")
        print(f"   - 出力ファイル: {output_file}")
        print("="*70)
        
    except Exception as e:
        print(f"❌ 処理エラー: {e}")
        save_progress(new_knowledge, output_file, total_processed, error=True)
    finally:
        conn.close()

def load_existing_horses_minimal():
    """既存馬名のみを最小限で読み込み"""
    existing_file = "data/dlogic_raw_knowledge.json"
    existing_horses = set()
    
    if not os.path.exists(existing_file):
        return existing_horses
    
    try:
        # ファイルの最初の部分から馬名を抽出（メモリ節約）
        with open(existing_file, 'r', encoding='utf-8') as f:
            # 最初の2MBのみ読み込み
            chunk = f.read(2 * 1024 * 1024)
            
            # "馬名": { のパターンを検索
            import re
            horse_names = re.findall(r'"([^"]+)": \{[^}]', chunk)
            existing_horses = set(horse_names)
            
        print(f"📋 既存馬名読み込み: {len(existing_horses)}頭 (部分読み込み)")
    except Exception as e:
        print(f"⚠️ 既存データ読み込みエラー: {e}")
        
    return existing_horses

def get_year_horses_fast(conn, year, existing_horses, limit):
    """年度の馬名を高速取得"""
    cursor = conn.cursor(dictionary=True)
    
    try:
        # シンプルなDISTINCTクエリ（GROUP BY回避）
        query = """
            SELECT DISTINCT BAMEI
            FROM umagoto_race_joho 
            WHERE KAISAI_NEN = %s
            AND BAMEI IS NOT NULL 
            AND BAMEI <> ''
            AND KAKUTEI_CHAKUJUN IS NOT NULL
            LIMIT %s
        """
        
        cursor.execute(query, (year, limit * 2))  # 余裕を持って多めに取得
        results = cursor.fetchall()
        
        # 既存馬を除外して新規馬のみ返す
        new_horses = []
        for row in results:
            horse_name = row['BAMEI']
            if horse_name not in existing_horses and len(new_horses) < limit:
                new_horses.append(horse_name)
        
        return new_horses
        
    except Exception as e:
        print(f"❌ {year}年馬名取得エラー: {e}")
        return []
    finally:
        cursor.close()

def extract_horse_past_5_races(conn, horse_name):
    """馬の過去5走データを効率的に抽出"""
    cursor = conn.cursor(dictionary=True)
    
    try:
        # 過去5走に必要な12項目データ
        query = """
            SELECT 
                KAKUTEI_CHAKUJUN as finish_position,
                TANSHO_ODDS as odds,
                TANSHO_NINKIJUN as popularity,
                SOHA_TIME as time,
                KAISAI_NEN as year,
                KAISAI_GAPPI as date,
                FUTAN_JURYO as weight,
                BATAIJU as horse_weight,
                ZOGEN_SA as weight_change,
                KISHUMEI_RYAKUSHO as jockey,
                CHOKYOSHIMEI_RYAKUSHO as trainer,
                SEIBETSU_CODE as sex
            FROM umagoto_race_joho 
            WHERE BAMEI = %s
            AND KAISAI_NEN >= '2020'
            AND KAKUTEI_CHAKUJUN IS NOT NULL
            ORDER BY KAISAI_NEN DESC, KAISAI_GAPPI DESC
            LIMIT 5
        """
        
        cursor.execute(query, (horse_name,))
        races = cursor.fetchall()
        
        if not races:
            return None
        
        # D-Logic用基本統計
        total_races = len(races)
        wins = sum(1 for race in races if race.get('finish_position') == 1)
        
        return {
            "name": horse_name,
            "total_races": total_races,
            "wins": wins,
            "win_rate": round(wins / total_races * 100, 1) if total_races > 0 else 0,
            "past_5_races": races,
            "processed_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ {horse_name}データ抽出エラー: {e}")
        return None
    finally:
        cursor.close()

def save_progress(knowledge, output_file, count, error=False):
    """進行状況保存"""
    knowledge["meta"]["current_count"] = count
    knowledge["meta"]["last_save"] = datetime.now().isoformat()
    if error:
        knowledge["meta"]["error_save"] = True
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(knowledge, f, ensure_ascii=False, indent=2)
    
    status = "エラー保存" if error else "中間保存"
    print(f"💾 {status}: {count}頭完了")

def finalize_knowledge(knowledge, output_file, count):
    """最終データ完成"""
    knowledge["meta"]["final_count"] = count
    knowledge["meta"]["completed"] = datetime.now().isoformat()
    knowledge["meta"]["status"] = "completed"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(knowledge, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    yearly_strategic_batch()