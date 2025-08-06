#!/usr/bin/env python3
"""
軽量版バッチ処理 - 大きなJSONファイルを避けて直接処理
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

# MySQL接続マネージャー
mysql_manager = get_mysql_manager()

def lightweight_batch_process():
    """軽量版バッチ処理"""
    start_time = time.time()
    print("🚀 軽量版バッチ処理開始")
    print(f"🕐 開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 接続テスト
    if not mysql_manager.test_connection():
        print("❌ MySQL接続テスト失敗")
        return
    print("✅ MySQL接続テスト成功")
    
    # 新しいナレッジファイルパス
    output_file = f"data/new_knowledge_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    # 既存のナレッジから処理済み馬名のみ取得（メモリ効率化）
    existing_horses = set()
    existing_file = "data/dlogic_raw_knowledge.json"
    
    print(f"📋 既存データの馬名のみ読み込み中...")
    if os.path.exists(existing_file):
        try:
            # ファイルを行ごとに読んで馬名のみ抽出
            with open(existing_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if '"horses"' in content:
                    # 簡単な文字列解析で馬名を抽出
                    start_idx = content.find('"horses": {')
                    if start_idx != -1:
                        horses_section = content[start_idx:start_idx + 100000]  # 最初の100KB程度
                        import re
                        horse_names = re.findall(r'"([^"]+)": \{', horses_section)
                        existing_horses = set(horse_names)
                        print(f"✅ 既存馬名 {len(existing_horses):,}頭を特定")
        except Exception as e:
            print(f"⚠️ 既存データ読み込みエラー: {e}")
    
    # データベースから未処理馬を取得
    print("🐎 未処理馬の抽出中...")
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
            LIMIT 1000
        """)
        
        unprocessed_horses = [h for h in horses if h['BAMEI'] not in existing_horses]
        total_unprocessed = len(unprocessed_horses)
        
        print(f"🎯 対象馬数: {len(horses):,}頭")
        print(f"🆕 未処理馬数: {total_unprocessed:,}頭")
        
        if total_unprocessed == 0:
            print("✅ 全ての馬の処理が完了しています")
            return
        
        # 新しいナレッジデータを作成
        new_knowledge = {
            "meta": {
                "version": "1.1",
                "created": datetime.now().isoformat(),
                "source": "lightweight_batch",
                "horses_count": 0
            },
            "horses": {}
        }
        
        processed = 0
        errors = 0
        batch_size = 50
        
        print(f"🏁 {total_unprocessed:,}頭の処理開始")
        
        for i, horse_data in enumerate(unprocessed_horses):
            horse_name = horse_data['BAMEI']
            
            try:
                # 軽量データ抽出
                raw_data = extract_horse_data_minimal(horse_name)
                
                if raw_data:
                    new_knowledge["horses"][horse_name] = raw_data
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
                        new_knowledge["meta"]["horses_count"] = processed
                        with open(output_file, 'w', encoding='utf-8') as f:
                            json.dump(new_knowledge, f, ensure_ascii=False, indent=2)
                        print(f"💾 中間保存: {processed:,}頭完了")
                else:
                    errors += 1
                    
            except Exception as e:
                errors += 1
                if errors % 10 == 0:
                    print(f"⚠️ エラー累計: {errors}件")
        
        # 最終保存
        new_knowledge["meta"]["horses_count"] = processed
        new_knowledge["meta"]["completed"] = datetime.now().isoformat()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(new_knowledge, f, ensure_ascii=False, indent=2)
        
        elapsed = time.time() - start_time
        
        print("\n" + "="*60)
        print("🎉 軽量版バッチ処理完了！")
        print(f"📊 結果:")
        print(f"   - 新規追加: {processed:,}頭")
        print(f"   - エラー数: {errors:,}件")
        print(f"   - 実行時間: {elapsed/60:.1f}分")
        print(f"   - 処理速度: {processed/(elapsed/60):.1f}頭/分")
        print(f"   - 出力ファイル: {output_file}")
        print("="*60)
        
    except Exception as e:
        print(f"❌ 処理エラー: {str(e)}")

def extract_horse_data_minimal(horse_name: str) -> Dict[str, Any]:
    """最小限のデータ抽出"""
    try:
        races = mysql_manager.execute_query("""
            SELECT 
                KAKUTEI_CHAKUJUN as finish,
                TANSHO_ODDS as odds,
                TANSHO_NINKIJUN as popularity,
                KAISAI_NEN as year,
                KAISAI_GAPPI as date
            FROM umagoto_race_joho 
            WHERE BAMEI = %s
            AND KAISAI_NEN >= '2020'
            AND KAKUTEI_CHAKUJUN IS NOT NULL
            ORDER BY KAISAI_NEN DESC, KAISAI_GAPPI DESC
            LIMIT 15
        """, (horse_name,))
        
        if not races:
            return None
        
        # 基本統計
        total_races = len(races)
        wins = sum(1 for race in races if race.get('finish') == 1)
        avg_odds = sum(float(race.get('odds', 0)) for race in races if race.get('odds')) / max(1, total_races)
        
        return {
            "name": horse_name,
            "total_races": total_races,
            "wins": wins,
            "win_rate": round(wins / total_races * 100, 1) if total_races > 0 else 0,
            "avg_odds": round(avg_odds, 1),
            "recent_races": races[:10],
            "processed_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ {horse_name}のデータ抽出エラー: {e}")
        return None

if __name__ == "__main__":
    lightweight_batch_process()