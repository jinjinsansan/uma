#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
地方競馬版（南関東）騎手ナレッジファイル週次差分更新スクリプト
JRA版と同じ方法で毎週更新
"""

import psycopg2
import json
import requests
import sys
import io
from datetime import datetime, timedelta
from collections import defaultdict

# Windows環境での文字化け対策
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# PostgreSQL接続情報（PC-KEIBA）
CONNECTION_PARAMS = {
    "host": "172.25.160.1",
    "port": "5432",
    "database": "pckeiba",
    "user": "postgres",
    "password": "postgres"
}

# 南関東競馬場コード
NANKAN_CODES = {
    '42': '大井',
    '43': '川崎',
    '44': '船橋',
    '45': '浦和'
}

def load_schedule_master():
    """スケジュールマスターファイルを読み込み"""
    try:
        schedule_file = '/mnt/e/dev/Cusor/chatbot/uma/data/nankan_schedule_master_2019_2025.json'
        with open(schedule_file, 'r', encoding='utf-8') as f:
            master = json.load(f)
        return master.get('schedule_data', {})
    except Exception as e:
        print(f"⚠️ スケジュールマスター読み込みエラー: {e}")
        return {}

def get_weekend_dates():
    """先週末の土日の日付を取得"""
    today = datetime.now()
    days_since_sunday = (today.weekday() + 1) % 7
    last_sunday = today - timedelta(days=days_since_sunday)
    last_saturday = last_sunday - timedelta(days=1)
    
    saturday = last_saturday.strftime('%m%d')
    sunday = last_sunday.strftime('%m%d')
    year = last_sunday.strftime('%Y')
    
    return year, saturday, sunday

def download_existing_jockey_knowledge():
    """既存の騎手ナレッジファイルをダウンロード"""
    print("📥 既存騎手ナレッジファイルをダウンロード中...")
    
    # CDN URL
    url = "https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/nankan_jockey_knowledge_20250907.json"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # データ構造を確認・修正
        # 正しい構造: {騎手名: {データ}, 騎手名: {データ}, ...}
        # 間違った構造: {metadata: {...}, jockeys: {騎手名: {データ}, ...}}
        
        jockey_data = {}
        
        # metadataやjockeysキーがある場合は除外
        for key, value in data.items():
            if key in ['metadata', 'jockeys']:
                # jockeysキーの中身があれば展開
                if key == 'jockeys' and isinstance(value, dict):
                    jockey_data.update(value)
            elif isinstance(value, dict):
                # 通常の騎手データ
                jockey_data[key] = value
        
        # データが空の場合は元のデータを使用
        if not jockey_data:
            jockey_data = data
        
        print(f"✅ {len(jockey_data)}名の騎手データをダウンロード完了")
        return jockey_data
    except Exception as e:
        print(f"⚠️ ダウンロードエラー: {e}")
        print("新規作成モードで開始します")
        return {}

def update_jockey_knowledge():
    """騎手ナレッジファイルを週末データで更新"""
    
    print("=" * 80)
    print("🏇 地方競馬版（南関東）騎手ナレッジファイル週次更新")
    print("=" * 80)
    
    try:
        # 1. 既存データをダウンロード
        jockey_data = download_existing_jockey_knowledge()
        
        # データ構造を初期化（必要に応じて）
        if not jockey_data:
            jockey_data = {}
        
        # 2. スケジュールマスター読み込み
        schedule_master = load_schedule_master()
        if schedule_master:
            print(f"✅ スケジュールマスター読み込み成功（{len(schedule_master)}日分）")
        
        # 3. 週末の日付を取得
        year, saturday, sunday = get_weekend_dates()
        print(f"\n📅 更新対象: {year}年 {saturday}(土) - {sunday}(日)")
        
        # 4. PostgreSQL接続
        print("\n📊 PostgreSQL接続中...")
        conn = psycopg2.connect(**CONNECTION_PARAMS)
        cur = conn.cursor()
        
        # 5. 週末の騎手成績データを取得
        query = """
        SELECT 
            se.kishumei_ryakusho,
            se.kaisai_nen,
            se.kaisai_tsukihi,
            se.keibajo_code,
            ra.kyori,
            ra.track_code,
            COALESCE(ra.babajotai_code_shiba, '0') || COALESCE(ra.babajotai_code_dirt, '0') as baba_code,
            se.wakuban,
            se.bamei,
            se.kakutei_chakujun,
            ra.shusso_tosu,
            COALESCE(nu.ketto_joho_01b, '') as sire
        FROM nvd_se se
        LEFT JOIN nvd_ra ra ON (
            se.kaisai_nen = ra.kaisai_nen
            AND se.kaisai_tsukihi = ra.kaisai_tsukihi
            AND se.keibajo_code = ra.keibajo_code
            AND se.race_bango = ra.race_bango
        )
        LEFT JOIN nvd_um nu ON se.ketto_toroku_bango = nu.ketto_toroku_bango
        WHERE se.kaisai_nen = %s
            AND (se.kaisai_tsukihi = %s OR se.kaisai_tsukihi = %s)
            AND se.keibajo_code IN ('42', '43', '44', '45')
            AND se.kishumei_ryakusho IS NOT NULL
            AND se.kishumei_ryakusho != ''
            AND se.kakutei_chakujun IS NOT NULL
            AND se.kakutei_chakujun != '00'
        ORDER BY se.kishumei_ryakusho, se.kaisai_tsukihi DESC
        """
        
        print("🔍 週末の騎手成績データ取得中...")
        cur.execute(query, (year, saturday, sunday))
        
        # 6. 新データを処理
        new_races = 0
        updated_jockeys = set()
        
        for row in cur:
            jockey_name = row[0].strip()
            kaisai_nen = row[1]
            kaisai_tsukihi = row[2]
            keibajo_code = row[3]
            kyori = row[4]
            track_code = row[5]
            baba_code = row[6]
            wakuban = row[7] if row[7] else '0'
            bamei = row[8].strip() if row[8] else ''
            chakujun = row[9]
            tosuu = row[10]
            sire = row[11].strip() if row[11] else ''
            
            # 騎手名設定
            if jockey_name not in jockey_data:
                jockey_data[jockey_name] = {
                    "name": jockey_name,
                    "venue_course_stats": {},
                    "track_condition_stats": {},
                    "post_position_stats": {},
                    "sire_stats": {},
                    "processed_at": datetime.now().isoformat(),
                    "overall_stats": {
                        "total_races_analyzed": 0,
                        "overall_fukusho_rate": 0.0
                    }
                }
            
            updated_jockeys.add(jockey_name)
            
            # レース結果データ
            position = int(chakujun) if chakujun and chakujun.isdigit() else 99
            total_horses = int(tosuu) if tosuu and tosuu.isdigit() else 18
            is_fukusho = position <= 3 and position > 0
            
            result_data = {
                "date": kaisai_nen + "-" + kaisai_tsukihi,
                "horse_name": bamei,
                "position": position,
                "total_horses": total_horses,
                "is_fukusho": is_fukusho
            }
            
            # 1. venue_course_stats（競馬場×距離別）
            keibajo_name = NANKAN_CODES.get(keibajo_code, keibajo_code)
            venue_key = f"{keibajo_name}_{kyori}m"
            
            if venue_key not in jockey_data[jockey_name]["venue_course_stats"]:
                jockey_data[jockey_name]["venue_course_stats"][venue_key] = {
                    "results": [],
                    "fukusho_rate": 0.0,
                    "race_count": 0
                }
            
            # 新レースを先頭に追加
            jockey_data[jockey_name]["venue_course_stats"][venue_key]["results"].insert(0, result_data)
            jockey_data[jockey_name]["venue_course_stats"][venue_key]["race_count"] += 1
            
            # 2. track_condition_stats（馬場状態別）
            track_key = f"{'芝' if track_code == '17' else 'ダート'}({baba_code})"
            
            if track_key not in jockey_data[jockey_name]["track_condition_stats"]:
                jockey_data[jockey_name]["track_condition_stats"][track_key] = {
                    "results": [],
                    "fukusho_rate": 0.0,
                    "race_count": 0
                }
            
            jockey_data[jockey_name]["track_condition_stats"][track_key]["results"].insert(0, result_data)
            jockey_data[jockey_name]["track_condition_stats"][track_key]["race_count"] += 1
            
            # 3. post_position_stats（枠番別）
            post_key = f"枠{wakuban}"
            
            if post_key not in jockey_data[jockey_name]["post_position_stats"]:
                jockey_data[jockey_name]["post_position_stats"][post_key] = {
                    "results": [],
                    "fukusho_rate": 0.0,
                    "race_count": 0
                }
            
            jockey_data[jockey_name]["post_position_stats"][post_key]["results"].insert(0, result_data)
            jockey_data[jockey_name]["post_position_stats"][post_key]["race_count"] += 1
            
            # 4. sire_stats（種牡馬別）
            if sire:
                if sire not in jockey_data[jockey_name]["sire_stats"]:
                    jockey_data[jockey_name]["sire_stats"][sire] = {
                        "results": [],
                        "fukusho_rate": 0.0,
                        "race_count": 0
                    }
                
                jockey_data[jockey_name]["sire_stats"][sire]["results"].insert(0, result_data)
                jockey_data[jockey_name]["sire_stats"][sire]["race_count"] += 1
            
            new_races += 1
        
        # 7. 複勝率を再計算
        print("\n📊 複勝率を再計算中...")
        for jockey_name in updated_jockeys:
            jockey = jockey_data[jockey_name]
            
            # venue_course_stats
            for venue_key, stats in jockey["venue_course_stats"].items():
                fukusho_count = sum(1 for r in stats["results"] if r["is_fukusho"])
                stats["fukusho_rate"] = round((fukusho_count / stats["race_count"] * 100), 1) if stats["race_count"] > 0 else 0.0
            
            # track_condition_stats
            for track_key, stats in jockey["track_condition_stats"].items():
                fukusho_count = sum(1 for r in stats["results"] if r["is_fukusho"])
                stats["fukusho_rate"] = round((fukusho_count / stats["race_count"] * 100), 1) if stats["race_count"] > 0 else 0.0
            
            # post_position_stats
            for post_key, stats in jockey["post_position_stats"].items():
                fukusho_count = sum(1 for r in stats["results"] if r["is_fukusho"])
                stats["fukusho_rate"] = round((fukusho_count / stats["race_count"] * 100), 1) if stats["race_count"] > 0 else 0.0
            
            # sire_stats
            for sire, stats in jockey["sire_stats"].items():
                fukusho_count = sum(1 for r in stats["results"] if r["is_fukusho"])
                stats["fukusho_rate"] = round((fukusho_count / stats["race_count"] * 100), 1) if stats["race_count"] > 0 else 0.0
            
            # processed_atを更新
            jockey["processed_at"] = datetime.now().isoformat()
        
        print(f"\n📊 更新結果:")
        print(f"  新規レース: {new_races}件")
        print(f"  更新された騎手: {len(updated_jockeys)}名")
        print(f"  総騎手数: {len(jockey_data)}名")
        
        # 8. 更新済みファイルを保存
        output_file = "nankan_jockey_knowledge_20250907.json"
        
        print(f"\n💾 ファイル保存中: {output_file}")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(jockey_data, f, ensure_ascii=False, indent=2)
        
        # ファイルサイズ確認
        import os
        file_size = os.path.getsize(output_file) / (1024 * 1024)
        print(f"✅ 保存完了: {file_size:.1f}MB")
        
        cur.close()
        conn.close()
        
        print("\n" + "=" * 80)
        print("🎉 騎手ナレッジ週次更新完了!")
        print("=" * 80)
        print(f"✅ 出力ファイル: {output_file}")
        print(f"✅ 新規レース数: {new_races}")
        print(f"✅ 総騎手数: {len(jockey_data)}")
        print("\n次のステップ:")
        print("1. ファイル名を nankan_jockey_knowledge_20250907.json に変更")
        print("2. このファイルをCloudflareにアップロード")
        
        return output_file
        
    except Exception as e:
        import traceback
        print(f"\n❌ エラー: {e}")
        print(f"詳細: {traceback.format_exc()}")
        return None

def main():
    """メイン処理"""
    print("🏇 地方競馬版（南関東）騎手ナレッジ週次更新処理開始")
    print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 騎手ナレッジファイル更新
    result = update_jockey_knowledge()
    
    if result:
        print("\n✅ 騎手ナレッジの更新が正常に完了しました")
    else:
        print("\n❌ 更新処理に失敗しました")

if __name__ == "__main__":
    main()
