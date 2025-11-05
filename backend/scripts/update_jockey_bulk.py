#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JRA騎手ナレッジファイル一括更新スクリプト
指定期間のデータを既存データに追加
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

# 国内競馬場コード
KEIBAJO_MAP = {
    '01': '札幌', '02': '函館', '03': '福島', '04': '新潟',
    '05': '東京', '06': '中山', '07': '中京', '08': '京都',
    '09': '阪神', '10': '小倉'
}

# 更新期間の設定
START_DATE = "2025-10-18"  # 開始日
END_DATE = "2025-11-04"    # 終了日（含む）

# Cloudflare CDN URL
JOCKEY_KNOWLEDGE_URL = "https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/jockey_knowledge.json"

def download_existing_jockey_knowledge():
    """既存の騎手ナレッジファイルをローカルから読み込み"""
    local_file = "/mnt/e/dev/Cusor/chatbot/uma/backend/jockey_knowledge_20251017.json"
    print(f"📥 既存騎手ナレッジファイルを読み込み中: {local_file}")
    
    try:
        with open(local_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"✅ {len(data)}名の騎手データを読み込み完了")
        return data
    except Exception as e:
        print(f"❌ 読み込みエラー: {e}")
        print("CDNからダウンロードを試行...")
        try:
            response = requests.get(JOCKEY_KNOWLEDGE_URL, timeout=60)
            response.raise_for_status()
            data = response.json()
            print(f"✅ {len(data)}名の騎手データをダウンロード完了")
            return data
        except Exception as e2:
            print(f"❌ ダウンロードエラー: {e2}")
            print("空のデータから開始します")
            return {}

def update_jockey_knowledge():
    """騎手ナレッジファイルを指定期間のデータで更新"""
    
    print("=" * 80)
    print("🏇 JRA騎手ナレッジファイル一括更新")
    print("=" * 80)
    
    try:
        # 1. 既存データを読み込み
        jockey_data = download_existing_jockey_knowledge()
        
        # データ構造を初期化
        if not jockey_data:
            jockey_data = {}
        
        # 2. 更新期間を表示
        print(f"\n📅 更新対象期間: {START_DATE} ～ {END_DATE}")
        
        # 3. PostgreSQL接続
        print("\n📊 PostgreSQL接続中...")
        conn = psycopg2.connect(**CONNECTION_PARAMS)
        cur = conn.cursor()
        
        # 4. 指定期間の騎手成績データを取得
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
            COALESCE(um.ketto_joho_01b, '') as sire
        FROM jvd_se se
        JOIN jvd_ra ra ON (
            se.kaisai_nen = ra.kaisai_nen
            AND se.kaisai_tsukihi = ra.kaisai_tsukihi
            AND se.keibajo_code = ra.keibajo_code
            AND se.race_bango = ra.race_bango
        )
        LEFT JOIN jvd_um um ON se.ketto_toroku_bango = um.ketto_toroku_bango
        WHERE se.kaisai_nen || '-' || 
              SUBSTRING(se.kaisai_tsukihi, 1, 2) || '-' || 
              SUBSTRING(se.kaisai_tsukihi, 3, 2) >= %s
            AND se.kaisai_nen || '-' || 
                SUBSTRING(se.kaisai_tsukihi, 1, 2) || '-' || 
                SUBSTRING(se.kaisai_tsukihi, 3, 2) <= %s
            AND se.keibajo_code IN ('01','02','03','04','05','06','07','08','09','10')
            AND se.kishumei_ryakusho IS NOT NULL
            AND se.kishumei_ryakusho != ''
            AND se.kakutei_chakujun IS NOT NULL
            AND se.kakutei_chakujun != '00'
        ORDER BY se.kishumei_ryakusho, se.kaisai_tsukihi DESC
        """
        
        print("🔍 指定期間の騎手成績データ取得中...")
        cur.execute(query, (START_DATE, END_DATE))
        
        # 5. 新データを処理
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
            keibajo_name = KEIBAJO_MAP.get(keibajo_code, keibajo_code)
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
            if sire and sire != '':
                if sire not in jockey_data[jockey_name]["sire_stats"]:
                    jockey_data[jockey_name]["sire_stats"][sire] = {
                        "results": [],
                        "fukusho_rate": 0.0,
                        "race_count": 0
                    }
                
                jockey_data[jockey_name]["sire_stats"][sire]["results"].insert(0, result_data)
                jockey_data[jockey_name]["sire_stats"][sire]["race_count"] += 1
            
            # 総合成績カウント
            jockey_data[jockey_name]["overall_stats"]["total_races_analyzed"] += 1
            new_races += 1
        
        # 6. 複勝率を再計算
        print("\n📊 複勝率を再計算中...")
        for jockey_name in updated_jockeys:
            jockey = jockey_data[jockey_name]
            
            # venue_course_statsの複勝率計算
            for venue_key in jockey["venue_course_stats"]:
                stats = jockey["venue_course_stats"][venue_key]
                if stats["race_count"] > 0:
                    fukusho_count = sum(1 for r in stats["results"] if r["is_fukusho"])
                    stats["fukusho_rate"] = round((fukusho_count / stats["race_count"]) * 100, 1)
            
            # track_condition_statsの複勝率計算
            for track_key in jockey["track_condition_stats"]:
                stats = jockey["track_condition_stats"][track_key]
                if stats["race_count"] > 0:
                    fukusho_count = sum(1 for r in stats["results"] if r["is_fukusho"])
                    stats["fukusho_rate"] = round((fukusho_count / stats["race_count"]) * 100, 1)
            
            # post_position_statsの複勝率計算
            for post_key in jockey["post_position_stats"]:
                stats = jockey["post_position_stats"][post_key]
                if stats["race_count"] > 0:
                    fukusho_count = sum(1 for r in stats["results"] if r["is_fukusho"])
                    stats["fukusho_rate"] = round((fukusho_count / stats["race_count"]) * 100, 1)
            
            # sire_statsの複勝率計算
            for sire_key in jockey["sire_stats"]:
                stats = jockey["sire_stats"][sire_key]
                if stats["race_count"] > 0:
                    fukusho_count = sum(1 for r in stats["results"] if r["is_fukusho"])
                    stats["fukusho_rate"] = round((fukusho_count / stats["race_count"]) * 100, 1)
            
            # 総合複勝率計算
            total_races = jockey["overall_stats"]["total_races_analyzed"]
            if total_races > 0:
                total_fukusho = 0
                for venue_stats in jockey["venue_course_stats"].values():
                    total_fukusho += sum(1 for r in venue_stats["results"] if r["is_fukusho"])
                
                jockey["overall_stats"]["overall_fukusho_rate"] = round((total_fukusho / total_races) * 100, 1)
            
            # processed_atを更新
            jockey["processed_at"] = datetime.now().isoformat()
        
        print(f"\n📊 更新結果:")
        print(f"  新規レース: {new_races}件")
        print(f"  更新された騎手: {len(updated_jockeys)}名")
        print(f"  総騎手数: {len(jockey_data)}名")
        
        # 7. 更新済みファイルを保存
        today = datetime.now().strftime("%Y%m%d")
        output_file = f"jockey_knowledge_{today}.json"
        
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
        print("🎉 一括更新完了!")
        print("=" * 80)
        print(f"✅ 出力ファイル: {output_file}")
        print(f"✅ 新規レース数: {new_races}")
        print(f"✅ 総騎手数: {len(jockey_data)}")
        print("\n次のステップ:")
        print("1. ローカルでバックエンドテスト")
        print("2. テスト成功後、Cloudflareにアップロード")
        
        return output_file
        
    except Exception as e:
        import traceback
        print(f"\n❌ エラー: {e}")
        print(f"詳細: {traceback.format_exc()}")
        return None

def main():
    """メイン処理"""
    print("🏇 JRA騎手ナレッジ一括更新処理開始")
    print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 騎手ナレッジファイル更新
    result = update_jockey_knowledge()
    
    if result:
        print("\n✅ すべての処理が正常に完了しました")
        return result
    else:
        print("\n❌ 更新処理に失敗しました")
        return None

if __name__ == "__main__":
    main()
