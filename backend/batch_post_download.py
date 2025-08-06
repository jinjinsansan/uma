#!/usr/bin/env python3
"""
ダウンロード完了後即座実行バッチ
最適化されたクエリで8000頭の現役馬データを効率収集
"""
import mysql.connector
import json
import time
import os
from datetime import datetime

def post_download_batch():
    """ダウンロード完了後の最適化バッチ"""
    start_time = time.time()
    print("🚀 ダウンロード完了後バッチ処理開始")
    print(f"🎯 目標: 現役馬8,000頭の過去5走データ")
    print(f"🕐 開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 事前テスト
    if not test_database_performance():
        print("❌ データベース性能テスト失敗")
        return
    
    # 既存馬名読み込み
    existing_horses = load_existing_horses_fast()
    print(f"📊 既存データ: {len(existing_horses):,}頭")
    
    # 出力ファイル
    output_file = f"data/post_download_batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    # ナレッジ構造
    knowledge = {
        "meta": {
            "created": datetime.now().isoformat(),
            "version": "post_download_1.0",
            "target_horses": 8000,
            "years_covered": "2020-2025"
        },
        "horses": {}
    }
    
    # MySQL接続（最適化設定）
    conn = mysql.connector.connect(
        host='172.25.160.1',
        port=3306,
        user='root',
        password='04050405Aoi-',
        database='mykeibadb',
        charset='utf8mb4',
        autocommit=True,
        buffered=True,
        use_unicode=True,
        sql_mode='TRADITIONAL'
    )
    
    try:
        total_processed = 0
        target_horses = 8000
        
        # 年度別効率処理
        years = ['2025', '2024', '2023', '2022', '2021', '2020']
        horses_per_year = target_horses // len(years)
        
        for year in years:
            if total_processed >= target_horses:
                break
            
            print(f"\n📅 {year}年処理開始 (目標: {horses_per_year}頭)")
            year_start = time.time()
            
            # 年度別馬名取得（最適化クエリ）
            year_horses = get_year_horses_optimized(conn, year, existing_horses, horses_per_year)
            print(f"   🐎 {year}年新規馬: {len(year_horses)}頭")
            
            # 馬データ一斉処理
            year_processed = process_horses_batch(conn, year_horses, knowledge)
            total_processed += year_processed
            
            # 既存リストに追加（重複回避）
            existing_horses.update(year_horses[:year_processed])
            
            year_time = time.time() - year_start
            print(f"   ✅ {year}年完了: {year_processed}頭, {year_time/60:.1f}分")
            
            # 進捗保存
            save_progress(knowledge, output_file, total_processed)
            
            print(f"📊 累計進捗: {total_processed:,}/{target_horses:,}頭 ({total_processed/target_horses*100:.1f}%)")
        
        # 最終完成
        finalize_batch(knowledge, output_file, total_processed)
        
        total_time = time.time() - start_time
        print("\n" + "="*70)
        print("🎉 ダウンロード完了後バッチ処理完了!")
        print(f"📊 最終結果:")
        print(f"   - 新規追加: {total_processed:,}頭")
        print(f"   - 総データ: {len(existing_horses)+total_processed:,}頭")
        print(f"   - 実行時間: {total_time/3600:.1f}時間")
        print(f"   - 処理速度: {total_processed/(total_time/3600):.0f}頭/時間")
        print("="*70)
        
    except Exception as e:
        print(f"❌ バッチ処理エラー: {e}")
        save_progress(knowledge, output_file, total_processed, error=True)
    finally:
        conn.close()

def test_database_performance():
    """データベース性能事前テスト"""
    try:
        conn = mysql.connector.connect(
            host='172.25.160.1',
            port=3306,
            user='root',
            password='04050405Aoi-',
            database='mykeibadb',
            charset='utf8mb4',
            connect_timeout=10
        )
        
        cursor = conn.cursor()
        start_time = time.time()
        cursor.execute('SELECT COUNT(*) FROM umagoto_race_joho LIMIT 1')
        result = cursor.fetchone()
        query_time = time.time() - start_time
        
        cursor.close()
        conn.close()
        
        print(f"📊 性能テスト: {query_time:.3f}秒, レコード数: {result[0]:,}件")
        
        if query_time < 2.0:
            print("✅ データベース性能良好")
            return True
        else:
            print("⚠️ データベース性能要改善")
            return False
            
    except Exception as e:
        print(f"❌ 性能テストエラー: {e}")
        return False

def load_existing_horses_fast():
    """既存馬名の高速読み込み"""
    existing_file = "data/dlogic_raw_knowledge.json"
    if not os.path.exists(existing_file):
        return set()
    
    try:
        with open(existing_file, 'r', encoding='utf-8') as f:
            # 最初の2MBから馬名抽出
            chunk = f.read(2 * 1024 * 1024)
            import re
            horse_names = re.findall(r'"([^"]{2,20})": \{', chunk)
            return set(horse_names)
    except:
        return set()

def get_year_horses_optimized(conn, year, existing_horses, limit):
    """年度馬名の最適化取得"""
    cursor = conn.cursor(dictionary=True)
    
    try:
        # インデックス活用の最適化クエリ
        query = """
            SELECT DISTINCT BAMEI
            FROM umagoto_race_joho 
            WHERE KAISAI_NEN = %s
            AND BAMEI IS NOT NULL 
            AND BAMEI <> ''
            AND LENGTH(BAMEI) > 1
            LIMIT %s
        """
        
        cursor.execute(query, (year, limit * 3))
        results = cursor.fetchall()
        
        # 既存馬除外
        new_horses = []
        for row in results:
            if row['BAMEI'] not in existing_horses and len(new_horses) < limit:
                new_horses.append(row['BAMEI'])
        
        return new_horses
        
    except Exception as e:
        print(f"❌ {year}年馬名取得エラー: {e}")
        return []
    finally:
        cursor.close()

def process_horses_batch(conn, horse_names, knowledge):
    """馬データの一括処理"""
    processed = 0
    
    for horse_name in horse_names:
        horse_data = extract_horse_races(conn, horse_name)
        if horse_data:
            knowledge["horses"][horse_name] = horse_data
            processed += 1
            
            if processed % 100 == 0:
                print(f"   📈 {processed}頭処理完了...")
    
    return processed

def extract_horse_races(conn, horse_name):
    """馬の過去レースデータ抽出"""
    cursor = conn.cursor(dictionary=True)
    
    try:
        query = """
            SELECT 
                KAKUTEI_CHAKUJUN as finish,
                TANSHO_ODDS as odds,
                TANSHO_NINKIJUN as popularity,
                SOHA_TIME as time,
                KAISAI_NEN as year,
                KAISAI_GAPPI as date
            FROM umagoto_race_joho 
            WHERE BAMEI = %s
            AND KAISAI_NEN >= '2020'
            AND KAKUTEI_CHAKUJUN IS NOT NULL
            ORDER BY KAISAI_NEN DESC, KAISAI_GAPPI DESC
            LIMIT 5
        """
        
        cursor.execute(query, (horse_name,))
        races = cursor.fetchall()
        
        if races:
            return {
                "name": horse_name,
                "race_count": len(races),
                "past_races": races,
                "processed_at": datetime.now().isoformat()
            }
            
    except Exception as e:
        print(f"❌ {horse_name}エラー: {e}")
    finally:
        cursor.close()
    
    return None

def save_progress(knowledge, output_file, count, error=False):
    """進捗保存"""
    knowledge["meta"]["current_count"] = count
    knowledge["meta"]["last_save"] = datetime.now().isoformat()
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(knowledge, f, ensure_ascii=False, indent=2)
    
    print(f"💾 進捗保存: {count}頭")

def finalize_batch(knowledge, output_file, count):
    """最終完成"""
    knowledge["meta"]["final_count"] = count
    knowledge["meta"]["completed"] = datetime.now().isoformat()
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(knowledge, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    post_download_batch()