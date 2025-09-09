#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
地方競馬版統合ナレッジファイル作成スクリプト
"""

import psycopg2
import json
import sys
import io
from datetime import datetime
from collections import defaultdict
import pandas as pd

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

def create_unified_knowledge():
    """統合ナレッジファイルを作成"""
    
    print("=" * 80)
    print("地方競馬版統合ナレッジファイル作成")
    print("=" * 80)
    
    try:
        conn = psycopg2.connect(**CONNECTION_PARAMS)
        cur = conn.cursor()
        
        # 対象期間（最新3年分）
        target_years = ['2022', '2023', '2024', '2025']
        
        # 南関東の馬データを取得するSQL
        query = """
        SELECT 
            se.bamei,
            se.kaisai_nen || se.kaisai_tsukihi || se.keibajo_code || 
                LPAD(se.race_bango::text, 2, '0') || '00' as race_code,
            se.kaisai_nen,
            se.kaisai_tsukihi as kaisai_gappi,
            LPAD(COALESCE(se.kakutei_chakujun, '00'), 2, '0') as kakutei_chakujun,
            LPAD(COALESCE(se.tansho_odds::text, '0000'), 4, '0') as tansho_odds,
            LPAD(COALESCE(se.tansho_ninkijun, '00'), 2, '0') as tansho_ninkijun,
            LPAD(COALESCE(se.futan_juryo::text, '000'), 3, '0') as futan_juryo,
            LPAD(COALESCE(se.bataiju::text, '000'), 3, '0') as bataiju,
            CASE 
                WHEN se.zogen_fugo = '-' THEN '-' || LPAD(COALESCE(se.zogen_sa::text, '00'), 2, '0')
                ELSE '+' || LPAD(COALESCE(se.zogen_sa::text, '00'), 2, '0')
            END as zogen_sa,
            COALESCE(se.kishumei_ryakusho, '') as kishumei_ryakusho,
            COALESCE(se.chokyoshimei_ryakusho, '') as chokyoshimei_ryakusho,
            LPAD(COALESCE(se.corner_1, '00'), 2, '0') as corner1_juni,
            LPAD(COALESCE(se.corner_2, '00'), 2, '0') as corner2_juni,
            LPAD(COALESCE(se.corner_3, '00'), 2, '0') as corner3_juni,
            LPAD(COALESCE(se.corner_4, '00'), 2, '0') as corner4_juni,
            COALESCE(se.soha_time, '0000') as soha_time,
            CASE 
                WHEN um.seinengappi IS NOT NULL THEN 
                    LPAD((se.kaisai_nen::int - SUBSTRING(um.seinengappi, 1, 4)::int)::text, 2, '0')
                ELSE '00'
            END as barei,
            COALESCE(um.seibetsu_code, '0') as seibetsu_code,
            se.keibajo_code,
            LPAD(se.race_bango::text, 2, '0') as race_bango,
            se.ketto_toroku_bango,
            CASE 
                WHEN se.time_sa LIKE '+%' THEN se.time_sa
                WHEN se.time_sa LIKE '-%' THEN se.time_sa
                ELSE '+' || LPAD(COALESCE(se.time_sa, '000'), 3, '0')
            END as time_sa,
            LPAD(COALESCE(ra.kyori::text, '0000'), 4, '0') as kyori,
            COALESCE(ra.track_code, '00') as track_code,
            COALESCE(ra.babajotai_code_shiba, '0') as shiba_babajotai_code,
            COALESCE(ra.babajotai_code_dirt, '0') as dirt_babajotai_code,
            COALESCE(ra.tenko_code, '0') as tenko_code,
            COALESCE(um.ketto_joho_01a, '') as sire,
            COALESCE(um.ketto_joho_01b, '') as dam,
            COALESCE(um.ketto_joho_02a, '') as broodmare_sire,
            CASE se.keibajo_code
                WHEN '42' THEN '浦和'
                WHEN '43' THEN '船橋'
                WHEN '44' THEN '大井'
                WHEN '45' THEN '川崎'
                ELSE se.keibajo_code
            END as track_name
        FROM nvd_se se
        JOIN nvd_ra ra ON (
            se.kaisai_nen = ra.kaisai_nen
            AND se.kaisai_tsukihi = ra.kaisai_tsukihi
            AND se.keibajo_code = ra.keibajo_code
            AND se.race_bango = ra.race_bango
        )
        LEFT JOIN nvd_um um ON se.ketto_toroku_bango = um.ketto_toroku_bango
        WHERE se.keibajo_code IN ('42', '43', '44', '45')
            AND se.kaisai_nen IN ('2022', '2023', '2024', '2025')
            AND se.bamei IS NOT NULL
            AND se.bamei != ''
        ORDER BY se.bamei, se.kaisai_nen DESC, se.kaisai_tsukihi DESC
        """
        
        print("データ取得中...")
        cur.execute(query)
        
        # 結果を馬ごとにグループ化
        horses_data = defaultdict(list)
        
        # カラム名を取得
        col_names = [
            "BAMEI", "RACE_CODE", "KAISAI_NEN", "KAISAI_GAPPI", "KAKUTEI_CHAKUJUN",
            "TANSHO_ODDS", "TANSHO_NINKIJUN", "FUTAN_JURYO", "BATAIJU", "ZOGEN_SA",
            "KISHUMEI_RYAKUSHO", "CHOKYOSHIMEI_RYAKUSHO", "CORNER1_JUNI", "CORNER2_JUNI",
            "CORNER3_JUNI", "CORNER4_JUNI", "SOHA_TIME", "BAREI", "SEIBETSU_CODE",
            "KEIBAJO_CODE", "RACE_BANGO", "KETTO_TOROKU_BANGO", "TIME_SA", "KYORI",
            "TRACK_CODE", "SHIBA_BABAJOTAI_CODE", "DIRT_BABAJOTAI_CODE", "TENKO_CODE",
            "sire", "dam", "broodmare_sire", "track_name"
        ]
        
        row_count = 0
        for row in cur:
            horse_name = row[0].strip()
            race_data = dict(zip(col_names, row))
            
            # 最新5走まで
            if len(horses_data[horse_name]) < 5:
                horses_data[horse_name].append(race_data)
            
            row_count += 1
            if row_count % 10000 == 0:
                print(f"  {row_count:,}件処理...")
        
        print(f"\n処理完了:")
        print(f"  総レコード数: {row_count:,}")
        print(f"  馬数: {len(horses_data):,}")
        
        # JSONファイルとして保存
        today = datetime.now().strftime("%Y%m%d")
        output_file = f"unified_knowledge_nankan_{today}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(dict(horses_data), f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ ファイル作成完了: {output_file}")
        
        # ファイルサイズ確認
        import os
        file_size = os.path.getsize(output_file) / (1024 * 1024)
        print(f"  ファイルサイズ: {file_size:.1f}MB")
        
        cur.close()
        conn.close()
        
        return output_file
        
    except Exception as e:
        import traceback
        print(f"エラー: {e}")
        print(f"詳細: {traceback.format_exc()}")
        return None

def create_jockey_knowledge():
    """騎手ナレッジファイルを作成"""
    
    print("\n" + "=" * 80)
    print("地方競馬版騎手ナレッジファイル作成")
    print("=" * 80)
    
    try:
        conn = psycopg2.connect(**CONNECTION_PARAMS)
        cur = conn.cursor()
        
        # 騎手別統計を集計
        query = """
        SELECT 
            se.kishumei_ryakusho,
            se.keibajo_code,
            ra.kyori,
            ra.track_code,
            se.wakuban,
            COUNT(*) as races,
            SUM(CASE WHEN se.kakutei_chakujun = '01' THEN 1 ELSE 0 END) as wins,
            SUM(CASE WHEN se.kakutei_chakujun IN ('01', '02', '03') THEN 1 ELSE 0 END) as top3
        FROM nvd_se se
        JOIN nvd_ra ra ON (
            se.kaisai_nen = ra.kaisai_nen
            AND se.kaisai_tsukihi = ra.kaisai_tsukihi
            AND se.keibajo_code = ra.keibajo_code
            AND se.race_bango = ra.race_bango
        )
        WHERE se.keibajo_code IN ('42', '43', '44', '45')
            AND se.kaisai_nen >= '2022'
            AND se.kishumei_ryakusho IS NOT NULL
            AND se.kishumei_ryakusho != ''
        GROUP BY 
            se.kishumei_ryakusho,
            se.keibajo_code,
            ra.kyori,
            ra.track_code,
            se.wakuban
        """
        
        print("騎手データ集計中...")
        cur.execute(query)
        
        # 騎手ごとのデータを整理
        jockey_data = defaultdict(lambda: {
            "venue_course_stats": {},
            "track_condition_stats": {},
            "post_position_stats": {},
            "overall_stats": {
                "total_races_analyzed": 0,
                "overall_win_rate": 0.0,
                "overall_top3_rate": 0.0
            },
            "last_updated": datetime.now().isoformat()
        })
        
        for row in cur:
            jockey_name = row[0].strip()
            keibajo = NANKAN_CODES.get(row[1], row[1])
            kyori = row[2]
            track_code = row[3]
            wakuban = row[4]
            races = row[5]
            wins = row[6]
            top3 = row[7]
            
            # 競馬場×距離別成績
            venue_course_key = f"{keibajo}_{kyori}"
            if venue_course_key not in jockey_data[jockey_name]["venue_course_stats"]:
                jockey_data[jockey_name]["venue_course_stats"][venue_course_key] = {
                    "races": 0,
                    "wins": 0,
                    "top3": 0,
                    "win_rate": 0.0,
                    "top3_rate": 0.0
                }
            
            stats = jockey_data[jockey_name]["venue_course_stats"][venue_course_key]
            stats["races"] += races
            stats["wins"] += wins
            stats["top3"] += top3
            if stats["races"] > 0:
                stats["win_rate"] = stats["wins"] / stats["races"]
                stats["top3_rate"] = stats["top3"] / stats["races"]
            
            # 総合成績更新
            overall = jockey_data[jockey_name]["overall_stats"]
            overall["total_races_analyzed"] += races
        
        # 総合勝率・複勝率を計算
        for jockey_name in jockey_data:
            total_races = jockey_data[jockey_name]["overall_stats"]["total_races_analyzed"]
            if total_races > 0:
                total_wins = sum(
                    s["wins"] for s in jockey_data[jockey_name]["venue_course_stats"].values()
                )
                total_top3 = sum(
                    s["top3"] for s in jockey_data[jockey_name]["venue_course_stats"].values()
                )
                jockey_data[jockey_name]["overall_stats"]["overall_win_rate"] = total_wins / total_races
                jockey_data[jockey_name]["overall_stats"]["overall_top3_rate"] = total_top3 / total_races
        
        print(f"\n騎手数: {len(jockey_data):,}")
        
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
        
        cur.close()
        conn.close()
        
        return output_file
        
    except Exception as e:
        import traceback
        print(f"エラー: {e}")
        print(f"詳細: {traceback.format_exc()}")
        return None

def main():
    """メイン処理"""
    print("🏇 地方競馬版ナレッジファイル作成開始")
    print("=" * 80)
    
    # 1. 統合ナレッジファイル作成
    unified_file = create_unified_knowledge()
    
    # 2. 騎手ナレッジファイル作成
    jockey_file = create_jockey_knowledge()
    
    print("\n" + "=" * 80)
    print("🎉 作成完了!")
    print("=" * 80)
    
    if unified_file:
        print(f"✅ 統合ナレッジ: {unified_file}")
    if jockey_file:
        print(f"✅ 騎手ナレッジ: {jockey_file}")
    
    print("\n【次のステップ】")
    print("1. 作成されたJSONファイルをCDNにアップロード")
    print("2. services/dlogic_raw_data_manager.pyのURLを更新")
    print("3. V2チャットで南関東データを利用可能に")

if __name__ == "__main__":
    main()