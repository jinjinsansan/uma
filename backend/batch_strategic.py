#!/usr/bin/env python3
"""
戦略的バッチ処理 - GROUP BYを回避した効率的な大量処理
281万件のデータから段階的に馬データを抽出
"""
import mysql.connector
import json
import time
import os
from datetime import datetime
from collections import defaultdict

def strategic_batch_process():
    """戦略的バッチ処理メイン"""
    start_time = time.time()
    print("🚀 戦略的バッチ処理開始")
    print(f"🕐 開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 出力ファイル
    output_file = f"data/strategic_batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    # 既存馬名の効率的読み込み（メモリ節約）
    existing_horses = load_existing_horses_efficiently()
    print(f"📊 既存馬名数: {len(existing_horses):,}頭")
    
    # 新しいナレッジデータ
    new_knowledge = {
        "meta": {
            "created": datetime.now().isoformat(),
            "version": "strategic_1.0",
            "source": "strategic_batch",
            "target_records": 0
        },
        "horses": {}
    }
    
    # 直接MySQL接続
    conn = mysql.connector.connect(
        host='172.25.160.1',
        port=3306,
        user='root',
        password='04050405Aoi-',
        database='mykeibadb',
        charset='utf8mb4',
        autocommit=True,
        buffered=True  # 重要：結果をバッファリング
    )
    
    try:
        processed_horses = 0
        total_records = 0
        
        # 戦略1: 年ごとに処理して負荷分散
        years = ['2024', '2023', '2022', '2021', '2020']
        
        for year in years:
            print(f"\n🗓️ {year}年のデータ処理開始")
            year_start = time.time()
            
            # その年の馬名を効率的に取得（GROUP BYなし）
            horses_this_year = get_horses_by_year_efficient(conn, year, existing_horses)
            print(f"   {year}年: {len(horses_this_year)}頭の新規馬を発見")
            
            # 各馬のデータを個別取得
            year_processed = 0
            for horse_name in horses_this_year:
                if year_processed >= 200:  # 年あたり最大200頭まで
                    break
                    
                horse_data = extract_horse_data_efficient(conn, horse_name, year)
                if horse_data:
                    new_knowledge["horses"][horse_name] = horse_data
                    year_processed += 1
                    total_records += len(horse_data.get('races', []))
                    
                    if year_processed % 20 == 0:
                        print(f"   📈 {year}年: {year_processed}頭処理完了")
            
            processed_horses += year_processed
            year_time = time.time() - year_start
            print(f"   ✅ {year}年完了: {year_processed}頭, {year_time:.1f}秒")
            
            # 中間保存
            if processed_horses % 100 == 0:
                save_intermediate_data(new_knowledge, output_file, processed_horses)
            
            # 早期終了条件（十分なデータが集まった場合）
            if processed_horses >= 1000:
                print(f"🎯 目標達成: {processed_horses}頭処理完了")
                break
        
        # 最終保存
        new_knowledge["meta"]["horses_count"] = processed_horses
        new_knowledge["meta"]["total_records"] = total_records
        new_knowledge["meta"]["completed"] = datetime.now().isoformat()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(new_knowledge, f, ensure_ascii=False, indent=2)
        
        elapsed = time.time() - start_time
        
        print("\n" + "="*60)
        print("🎉 戦略的バッチ処理完了！")
        print(f"📊 処理結果:")
        print(f"   - 新規追加馬: {processed_horses:,}頭")
        print(f"   - 総レコード数: {total_records:,}件")
        print(f"   - 実行時間: {elapsed/60:.1f}分")
        print(f"   - 処理速度: {processed_horses/(elapsed/60):.1f}頭/分")
        print(f"   - 出力ファイル: {output_file}")
        print("="*60)
        
    except Exception as e:
        print(f"❌ 処理エラー: {e}")
    finally:
        conn.close()

def load_existing_horses_efficiently():
    """既存馬名のみを効率的に読み込み"""
    existing_horses = set()
    existing_file = "data/dlogic_raw_knowledge.json"
    
    if not os.path.exists(existing_file):
        return existing_horses
    
    try:
        # ファイルサイズチェック
        file_size = os.path.getsize(existing_file)
        if file_size > 50 * 1024 * 1024:  # 50MB以上なら部分読み込み
            print("📋 大きなファイルを部分読み込み中...")
            with open(existing_file, 'r', encoding='utf-8') as f:
                # 最初の1MBから馬名を抽出
                chunk = f.read(1024 * 1024)
                import re
                horse_names = re.findall(r'"([^"]+)": \{', chunk)
                existing_horses = set(horse_names)
        else:
            print("📋 既存データ読み込み中...")
            with open(existing_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                existing_horses = set(data.get("horses", {}).keys())
    except Exception as e:
        print(f"⚠️ 既存データ読み込みエラー: {e}")
    
    return existing_horses

def get_horses_by_year_efficient(conn, year, existing_horses):
    """年ごとに馬名を効率的に取得（GROUP BYなし）"""
    cursor = conn.cursor(dictionary=True)
    
    # DISTINCT利用でGROUP BYを回避
    query = """
        SELECT DISTINCT BAMEI
        FROM umagoto_race_joho 
        WHERE KAISAI_NEN = %s
        AND BAMEI IS NOT NULL 
        AND BAMEI <> ''
        AND KAKUTEI_CHAKUJUN IS NOT NULL
        LIMIT 1000
    """
    
    cursor.execute(query, (year,))
    results = cursor.fetchall()
    cursor.close()
    
    # 既存馬を除外
    new_horses = [row['BAMEI'] for row in results if row['BAMEI'] not in existing_horses]
    return new_horses[:300]  # 年あたり最大300頭

def extract_horse_data_efficient(conn, horse_name, primary_year):
    """効率的な馬データ抽出"""
    cursor = conn.cursor(dictionary=True)
    
    try:
        # 特定の馬の最新レースデータのみ取得
        query = """
            SELECT 
                KAKUTEI_CHAKUJUN as finish,
                TANSHO_ODDS as odds,
                TANSHO_NINKIJUN as popularity,
                KAISAI_NEN as year,
                KAISAI_GAPPI as date,
                SOHA_TIME as time
            FROM umagoto_race_joho 
            WHERE BAMEI = %s
            AND KAISAI_NEN >= '2020'
            AND KAKUTEI_CHAKUJUN IS NOT NULL
            ORDER BY KAISAI_NEN DESC, KAISAI_GAPPI DESC
            LIMIT 12
        """
        
        cursor.execute(query, (horse_name,))
        races = cursor.fetchall()
        
        if not races:
            return None
        
        # 基本統計計算
        total_races = len(races)
        wins = sum(1 for race in races if race.get('finish') == 1)
        avg_odds = sum(float(race.get('odds', 0)) for race in races if race.get('odds')) / max(1, total_races)
        
        return {
            "name": horse_name,
            "primary_year": primary_year,
            "total_races": total_races,
            "wins": wins,
            "win_rate": round(wins / total_races * 100, 1) if total_races > 0 else 0,
            "avg_odds": round(avg_odds, 1),
            "races": races[:8],  # 最新8レースのみ保存
            "processed_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ {horse_name}のデータ抽出エラー: {e}")
        return None
    finally:
        cursor.close()

def save_intermediate_data(knowledge, output_file, count):
    """中間データ保存"""
    knowledge["meta"]["intermediate_save"] = datetime.now().isoformat()
    knowledge["meta"]["current_count"] = count
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(knowledge, f, ensure_ascii=False, indent=2)
    print(f"💾 中間保存完了: {count}頭")

if __name__ == "__main__":
    strategic_batch_process()