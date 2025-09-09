#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
地方競馬版騎手ナレッジファイル作成スクリプト（JRA版と完全同一形式）
"""

import psycopg2
import json
import sys
import io
from datetime import datetime
from collections import defaultdict

# Windows環境での文字化け対策
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# データベース接続情報
CONNECTION_PARAMS = {
    "host": "172.25.160.1",
    "port": "5432",
    "database": "pckeiba",
    "user": "postgres",
    "password": "postgres"
}

# 南関東競馬場
NANKAN_CODES = {
    '42': '浦和',
    '43': '船橋',
    '44': '大井',
    '45': '川崎'
}

def create_jockey_knowledge():
    """騎手ナレッジファイルを作成（JRA版と完全同一形式）"""
    
    print("=" * 80)
    print("地方競馬版騎手ナレッジファイル作成（JRA版完全互換）")
    print("=" * 80)
    
    try:
        conn = psycopg2.connect(**CONNECTION_PARAMS)
        cur = conn.cursor()
        
        # 対象期間（7年分）
        target_years = ['2019', '2020', '2021', '2022', '2023', '2024', '2025']
        
        print(f"対象期間: {target_years[0]}年 〜 {target_years[-1]}年（7年分）")
        print("対象競馬場: 南関東4場")
        print("-" * 60)
        
        # 騎手別データを取得するSQL
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
            um.ketto_joho_01a as sire
        FROM nvd_se se
        JOIN nvd_ra ra ON (
            se.kaisai_nen = ra.kaisai_nen
            AND se.kaisai_tsukihi = ra.kaisai_tsukihi
            AND se.keibajo_code = ra.keibajo_code
            AND se.race_bango = ra.race_bango
        )
        LEFT JOIN nvd_um um ON se.ketto_toroku_bango = um.ketto_toroku_bango
        WHERE se.keibajo_code IN ('42', '43', '44', '45')
            AND se.kaisai_nen IN ('2019', '2020', '2021', '2022', '2023', '2024', '2025')
            AND se.kishumei_ryakusho IS NOT NULL
            AND se.kishumei_ryakusho != ''
        ORDER BY se.kishumei_ryakusho, se.kaisai_nen DESC, se.kaisai_tsukihi DESC
        """
        
        print("データ取得中...")
        cur.execute(query)
        
        # 騎手ごとのデータを整理（JRA版と完全同一構造）
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
        
        row_count = 0
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
            sire = row[11] if row[11] else '不明'
            
            # 騎手名設定
            if not jockey_data[jockey_name]["name"]:
                jockey_data[jockey_name]["name"] = jockey_name
            
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
            
            # 最新5レースまで保存（JRA版と同様）
            if len(jockey_data[jockey_name]["venue_course_stats"][venue_key]["results"]) < 5:
                jockey_data[jockey_name]["venue_course_stats"][venue_key]["results"].append(result_data)
                jockey_data[jockey_name]["venue_course_stats"][venue_key]["race_count"] += 1
            
            # 2. track_condition_stats（馬場状態別）
            # トラックコード(17=芝、24=ダート)と馬場状態を組み合わせ
            track_key = f"{'芝' if track_code == '17' else 'ダート'}({baba_code})"
            
            if track_key not in jockey_data[jockey_name]["track_condition_stats"]:
                jockey_data[jockey_name]["track_condition_stats"][track_key] = {
                    "results": [],
                    "fukusho_rate": 0.0,
                    "race_count": 0
                }
            
            if len(jockey_data[jockey_name]["track_condition_stats"][track_key]["results"]) < 5:
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
            
            if len(jockey_data[jockey_name]["post_position_stats"][post_key]["results"]) < 5:
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
                
                if len(jockey_data[jockey_name]["sire_stats"][sire]["results"]) < 5:
                    jockey_data[jockey_name]["sire_stats"][sire]["results"].append(result_data)
                    jockey_data[jockey_name]["sire_stats"][sire]["race_count"] += 1
            
            # 総合成績カウント
            jockey_data[jockey_name]["overall_stats"]["total_races_analyzed"] += 1
            
            row_count += 1
            if row_count % 10000 == 0:
                print(f"  {row_count:,}件処理...")
        
        print(f"\n処理完了:")
        print(f"  総レコード数: {row_count:,}")
        print(f"  騎手数: {len(jockey_data):,}")
        
        # 各統計の複勝率を計算
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
                # すべてのresultsから複勝数をカウント
                total_fukusho = 0
                for venue_stats in jockey["venue_course_stats"].values():
                    total_fukusho += sum(1 for r in venue_stats["results"] if r["is_fukusho"])
                
                jockey["overall_stats"]["overall_fukusho_rate"] = round((total_fukusho / total_races) * 100, 1)
        
        # JSONファイルとして保存
        today = datetime.now().strftime("%Y%m%d")
        output_file = f"jockey_knowledge_nankan_{today}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(dict(jockey_data), f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ ファイル作成完了: {output_file}")
        
        # ファイルサイズ確認
        import os
        file_size = os.path.getsize(output_file) / (1024 * 1024)
        print(f"  ファイルサイズ: {file_size:.1f}MB")
        
        # サンプル表示
        print("\n【サンプル騎手データ】")
        sample_jockey = list(jockey_data.keys())[0]
        print(f"騎手名: {sample_jockey}")
        print(f"総騎乗数: {jockey_data[sample_jockey]['overall_stats']['total_races_analyzed']}")
        print(f"総合複勝率: {jockey_data[sample_jockey]['overall_stats']['overall_fukusho_rate']}%")
        
        cur.close()
        conn.close()
        
        return output_file, len(jockey_data)
        
    except Exception as e:
        import traceback
        print(f"エラー: {e}")
        print(f"詳細: {traceback.format_exc()}")
        return None, 0

def main():
    """メイン処理"""
    print("🏇 地方競馬版騎手ナレッジファイル作成（JRA版完全互換）")
    print("=" * 80)
    print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 騎手ナレッジファイル作成
    output_file, jockey_count = create_jockey_knowledge()
    
    if output_file:
        print("\n" + "=" * 80)
        print("🎉 作成完了!")
        print("=" * 80)
        print(f"✅ 騎手ナレッジ: {output_file}")
        print(f"✅ 総騎手数: {jockey_count:,}名")
        print(f"✅ データ期間: 7年（2019-2025）")
        print(f"✅ 形式: JRA版と完全同一")
        print("\n【次のステップ】")
        print("1. CDNへのアップロード")
        print("2. システムへの組み込み")
    else:
        print("\n❌ ファイル作成に失敗しました")

if __name__ == "__main__":
    main()