#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
南関東騎手ナレッジファイル作成スクリプト（正規版）
大井・川崎・船橋・浦和の騎手成績を集計
JRA騎手ナレッジファイルと完全互換
"""

import psycopg2
import json
import sys
import io
import time
from datetime import datetime
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
NANKAN_KEIBAJO_MAP = {
    '42': '大井',
    '43': '川崎',
    '44': '船橋',
    '45': '浦和'
}

def create_nankan_jockey_knowledge():
    """南関東騎手ナレッジファイル作成"""
    
    print("=" * 80)
    print("🏇 南関東騎手ナレッジファイル作成（正規版）")
    print("=" * 80)
    
    start_time = time.time()
    
    try:
        # PostgreSQL接続
        print("\n📊 PostgreSQL接続中...")
        conn = psycopg2.connect(**CONNECTION_PARAMS)
        cur = conn.cursor()
        
        # nvdテーブル確認
        print("🔍 nvdテーブル確認中...")
        cur.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_name IN ('nvd_se', 'nvd_ra', 'nvd_um')
        """)
        table_count = cur.fetchone()[0]
        print(f"✅ 必要なテーブル {table_count}/3 を確認")
        
        # 騎手成績データ取得クエリ
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
        FROM nvd_se se
        JOIN nvd_ra ra ON (
            se.kaisai_nen = ra.kaisai_nen
            AND se.kaisai_tsukihi = ra.kaisai_tsukihi
            AND se.keibajo_code = ra.keibajo_code
            AND se.race_bango = ra.race_bango
        )
        LEFT JOIN nvd_um um ON se.ketto_toroku_bango = um.ketto_toroku_bango
        WHERE se.kaisai_nen BETWEEN '2019' AND '2025'
            AND se.keibajo_code IN ('42','43','44','45')
            AND se.kishumei_ryakusho IS NOT NULL
            AND se.kishumei_ryakusho != ''
            AND se.kakutei_chakujun IS NOT NULL
            AND se.kakutei_chakujun != '00'
        ORDER BY se.kishumei_ryakusho, se.kaisai_tsukihi DESC
        """
        
        print("\n🔍 南関東4場の騎手成績データ取得中...")
        print("  対象: 大井(42)・川崎(43)・船橋(44)・浦和(45)")
        print("  期間: 2019年～2025年")
        
        query_start = time.time()
        cur.execute(query)
        query_end = time.time()
        print(f"✅ クエリ実行時間: {query_end - query_start:.2f}秒")
        
        # データ処理
        print("\n📊 騎手成績データ処理中...")
        jockey_data = defaultdict(lambda: {
            "name": "",
            "venue_course_stats": {},
            "track_condition_stats": {},
            "post_position_stats": {},
            "sire_stats": {},
            "processed_at": datetime.now().isoformat(),
            "overall_stats": {
                "total_races_analyzed": 0,
                "overall_fukusho_rate": 0.0
            }
        })
        
        total_races = 0
        jockey_race_count = defaultdict(int)
        
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
            if jockey_data[jockey_name]["name"] == "":
                jockey_data[jockey_name]["name"] = jockey_name
            
            # レース結果データ
            position = int(chakujun) if chakujun and chakujun.isdigit() else 99
            total_horses = int(tosuu) if tosuu and tosuu.isdigit() else 18
            is_fukusho = position <= 3 and position > 0
            
            result_data = {
                "date": kaisai_nen + "-" + kaisai_tsukihi[:2] + kaisai_tsukihi[2:],
                "horse_name": bamei,
                "position": position,
                "total_horses": total_horses,
                "is_fukusho": is_fukusho
            }
            
            # 1. venue_course_stats（競馬場×距離別）
            keibajo_name = NANKAN_KEIBAJO_MAP.get(keibajo_code, keibajo_code)
            venue_key = f"{keibajo_name}_{kyori}m"
            
            if venue_key not in jockey_data[jockey_name]["venue_course_stats"]:
                jockey_data[jockey_name]["venue_course_stats"][venue_key] = {
                    "results": [],
                    "fukusho_rate": 0.0,
                    "race_count": 0
                }
            
            jockey_data[jockey_name]["venue_course_stats"][venue_key]["results"].append(result_data)
            jockey_data[jockey_name]["venue_course_stats"][venue_key]["race_count"] += 1
            
            # 2. track_condition_stats（馬場状態別）
            track_key = f"{'芝' if track_code == '17' else 'ダート'}({baba_code})"
            
            if track_key not in jockey_data[jockey_name]["track_condition_stats"]:
                jockey_data[jockey_name]["track_condition_stats"][track_key] = {
                    "results": [],
                    "fukusho_rate": 0.0,
                    "race_count": 0
                }
            
            jockey_data[jockey_name]["track_condition_stats"][track_key]["results"].append(result_data)
            jockey_data[jockey_name]["track_condition_stats"][track_key]["race_count"] += 1
            
            # 3. post_position_stats（枠番別）
            post_key = f"枠{wakuban}"
            
            if post_key not in jockey_data[jockey_name]["post_position_stats"]:
                jockey_data[jockey_name]["post_position_stats"][post_key] = {
                    "results": [],
                    "fukusho_rate": 0.0,
                    "race_count": 0
                }
            
            jockey_data[jockey_name]["post_position_stats"][post_key]["results"].append(result_data)
            jockey_data[jockey_name]["post_position_stats"][post_key]["race_count"] += 1
            
            # 4. sire_stats（種牡馬別）
            if sire and sire != '':
                if sire not in jockey_data[jockey_name]["sire_stats"]:
                    jockey_data[jockey_name]["sire_stats"][sire] = {
                        "results": [],
                        "fukusho_rate": 0.0,
                        "race_count": 0
                    }
                
                jockey_data[jockey_name]["sire_stats"][sire]["results"].append(result_data)
                jockey_data[jockey_name]["sire_stats"][sire]["race_count"] += 1
            
            # 総合成績カウント
            jockey_data[jockey_name]["overall_stats"]["total_races_analyzed"] += 1
            jockey_race_count[jockey_name] += 1
            total_races += 1
            
            # 進捗表示
            if total_races % 10000 == 0:
                print(f"  {total_races}レース処理済み...")
        
        # 複勝率を計算
        print("\n📊 複勝率を計算中...")
        for jockey_name in jockey_data:
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
                
                # 重複カウントを防ぐため、venue_course_statsのデータのみ使用
                jockey["overall_stats"]["overall_fukusho_rate"] = round((total_fukusho / total_races) * 100, 1)
        
        # 統計情報表示
        print("\n📊 処理結果:")
        print(f"  総騎手数: {len(jockey_data)}名")
        print(f"  総レース数: {total_races}件")
        
        # 騎乗数上位騎手表示
        print("\n🏆 騎乗数上位騎手:")
        top_jockeys = sorted(jockey_race_count.items(), key=lambda x: x[1], reverse=True)[:10]
        for i, (jockey_name, count) in enumerate(top_jockeys[:5], 1):
            fukusho_rate = jockey_data[jockey_name]["overall_stats"]["overall_fukusho_rate"]
            print(f"  {i}. {jockey_name}: {count}騎乗 (複勝率 {fukusho_rate}%)")
        
        # ファイル保存
        today = datetime.now().strftime("%Y%m%d")
        output_file = f"nankan_jockey_knowledge_{today}.json"
        
        print(f"\n💾 ファイル保存中: {output_file}")
        save_start = time.time()
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(dict(jockey_data), f, ensure_ascii=False, indent=2)
        save_end = time.time()
        
        # ファイルサイズ確認
        import os
        file_size = os.path.getsize(output_file) / (1024 * 1024)
        
        cur.close()
        conn.close()
        
        total_time = time.time() - start_time
        
        print("\n" + "=" * 80)
        print("🎉 南関東騎手ナレッジファイル作成完了！")
        print("=" * 80)
        print(f"✅ ファイル名: {output_file}")
        print(f"✅ ファイルサイズ: {file_size:.1f}MB")
        print(f"✅ 処理時間: {total_time:.2f}秒")
        print(f"✅ 総騎手数: {len(jockey_data)}名")
        print(f"✅ 総レース数: {total_races}件")
        print("\n【データ構造】")
        print("• venue_course_stats: 競馬場×距離別成績")
        print("• track_condition_stats: 馬場状態別成績")
        print("• post_position_stats: 枠番別成績")
        print("• sire_stats: 種牡馬別成績")
        print("• JRA騎手ナレッジと完全互換")
        
        return output_file
        
    except Exception as e:
        import traceback
        print(f"\n❌ エラー: {e}")
        print(f"詳細: {traceback.format_exc()}")
        return None

def main():
    """メイン処理"""
    print("🏇 南関東騎手ナレッジファイル作成開始")
    print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    result = create_nankan_jockey_knowledge()
    
    if result:
        print("\n✅ 正常に完了しました")
        print("次のステップ:")
        print("1. 作成されたファイルの動作確認")
        print("2. エンジンでの互換性テスト")
        print("3. 本番環境へのアップロード")
    else:
        print("\n❌ 作成に失敗しました")

if __name__ == "__main__":
    main()