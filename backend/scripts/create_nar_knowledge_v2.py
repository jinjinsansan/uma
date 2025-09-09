#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
地方競馬版統合ナレッジファイル作成スクリプト（本番版）
- 7年分のデータ（2019-2025）
- 各馬最新9走まで
- JRA版と完全互換
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

def create_unified_knowledge():
    """統合ナレッジファイルを作成（7年分、最大9走）"""
    
    print("=" * 80)
    print("地方競馬版統合ナレッジファイル作成（本番版）")
    print("=" * 80)
    
    try:
        conn = psycopg2.connect(**CONNECTION_PARAMS)
        cur = conn.cursor()
        
        # 対象期間（7年分）
        target_years = ['2019', '2020', '2021', '2022', '2023', '2024', '2025']
        
        print(f"対象期間: {target_years[0]}年 〜 {target_years[-1]}年（7年分）")
        print("最大取得走数: 9走/馬")
        print("対象競馬場: 南関東4場")
        print("-" * 60)
        
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
                WHEN um.seinengappi IS NOT NULL AND um.seinengappi != '' THEN 
                    LPAD(GREATEST(0, (se.kaisai_nen::int - SUBSTRING(um.seinengappi, 1, 4)::int))::text, 2, '0')
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
            AND se.kaisai_nen IN ('2019', '2020', '2021', '2022', '2023', '2024', '2025')
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
        total_races_stored = 0
        
        for row in cur:
            horse_name = row[0].strip()
            race_data = dict(zip(col_names, row))
            
            # 最新9走まで
            if len(horses_data[horse_name]) < 9:
                horses_data[horse_name].append(race_data)
                total_races_stored += 1
            
            row_count += 1
            if row_count % 10000 == 0:
                print(f"  {row_count:,}件処理...")
        
        # 統計情報
        race_counts = {}
        for horse_name, races in horses_data.items():
            count = len(races)
            if count not in race_counts:
                race_counts[count] = 0
            race_counts[count] += 1
        
        print(f"\n処理完了:")
        print(f"  総レコード数: {row_count:,}")
        print(f"  馬数: {len(horses_data):,}")
        print(f"  保存レース数: {total_races_stored:,}")
        
        print(f"\n走数別馬数分布:")
        for i in range(1, 10):
            if i in race_counts:
                print(f"  {i}走: {race_counts[i]:,}頭")
        
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
        
        return output_file, len(horses_data)
        
    except Exception as e:
        import traceback
        print(f"エラー: {e}")
        print(f"詳細: {traceback.format_exc()}")
        return None, 0

def main():
    """メイン処理"""
    print("🏇 地方競馬版統合ナレッジファイル作成（本番版）")
    print("=" * 80)
    print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 統合ナレッジファイル作成
    output_file, horse_count = create_unified_knowledge()
    
    if output_file:
        print("\n" + "=" * 80)
        print("🎉 作成完了!")
        print("=" * 80)
        print(f"✅ 統合ナレッジ: {output_file}")
        print(f"✅ 総馬数: {horse_count:,}頭")
        print(f"✅ データ期間: 7年（2019-2025）")
        print(f"✅ 最大走数: 9走/馬")
        print("\n【次のステップ】")
        print("1. 騎手ナレッジファイルの作成")
        print("2. CDNへのアップロード")
        print("3. システムへの組み込み")
    else:
        print("\n❌ ファイル作成に失敗しました")

if __name__ == "__main__":
    main()