#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JRA統合ナレッジファイル一括更新スクリプト
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

def normalize_corner_value(value):
    """コーナー通過順位を正規化（欠損はNone）"""
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    try:
        numeric = int(s)
    except ValueError:
        return None
    if numeric <= 0:
        return None
    return f"{numeric:02d}"

def fill_corner_values(corner_values):
    """欠損時に後続コーナーから補完した通過順位を返す"""
    normalized = [normalize_corner_value(v) for v in corner_values]
    filled = []
    fallback_used = False

    for idx in range(4):
        value = normalized[idx]
        replaced_with_later = False

        if value is None:
            for lookahead in range(idx + 1, 4):
                next_value = normalized[lookahead]
                if next_value is not None:
                    value = next_value
                    replaced_with_later = True
                    break

        if value is None:
            value = '00'

        if replaced_with_later:
            fallback_used = True

        filled.append(value)

    return filled, fallback_used

# Cloudflare CDN URL
UNIFIED_KNOWLEDGE_URL = "https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/unified_knowledge_20250903.json"

def download_existing_knowledge():
    """既存のナレッジファイルをローカルから読み込み"""
    local_file = "/mnt/e/dev/Cusor/chatbot/uma/backend/unified_knowledge_20251017.json"
    print(f"📥 既存ナレッジファイルを読み込み中: {local_file}")
    
    try:
        with open(local_file, 'r', encoding='utf-8') as f:
            full_data = json.load(f)
        horses_data = full_data.get("horses", full_data)
        print(f"✅ {len(horses_data)}頭のデータを読み込み完了")
        return horses_data
    except Exception as e:
        print(f"❌ 読み込みエラー: {e}")
        print("CDNからダウンロードを試行...")
        try:
            response = requests.get(UNIFIED_KNOWLEDGE_URL, timeout=60)
            response.raise_for_status()
            full_data = response.json()
            horses_data = full_data.get("horses", full_data)
            print(f"✅ {len(horses_data)}頭のデータをダウンロード完了")
            return horses_data
        except Exception as e2:
            print(f"❌ ダウンロードエラー: {e2}")
            print("空のデータから開始します")
            return {}

def update_unified_knowledge():
    """統合ナレッジファイルを指定期間のデータで更新"""
    
    print("=" * 80)
    print("🏇 JRA統合ナレッジファイル一括更新")
    print("=" * 80)
    
    try:
        # 1. 既存データをダウンロード
        horses_data = download_existing_knowledge()
        
        # 2. 更新期間を表示
        print(f"\n📅 更新対象期間: {START_DATE} ～ {END_DATE}")
        
        # 3. PostgreSQL接続
        print("\n📊 PostgreSQL接続中...")
        conn = psycopg2.connect(**CONNECTION_PARAMS)
        cur = conn.cursor()
        
        # 4. 指定期間のレースデータを取得
        query = """
        SELECT 
            se.bamei,
            se.kaisai_nen || se.kaisai_tsukihi || se.keibajo_code || 
                LPAD(se.race_bango::text, 2, '0') || LPAD(se.umaban::text, 2, '0') as race_code,
            se.kaisai_nen,
            se.kaisai_tsukihi as kaisai_gappi,
            CASE 
                WHEN se.kakutei_chakujun IS NULL OR se.kakutei_chakujun = '' THEN '00'
                ELSE LPAD(se.kakutei_chakujun::text, 2, '0')
            END as kakutei_chakujun,
            CASE 
                WHEN se.tansho_odds IS NULL OR se.tansho_odds = '' THEN '0000'
                ELSE LPAD(se.tansho_odds::text, 4, '0')
            END as tansho_odds,
            CASE 
                WHEN se.tansho_ninkijun IS NULL OR se.tansho_ninkijun = '' THEN '00'
                ELSE LPAD(se.tansho_ninkijun::text, 2, '0')
            END as tansho_ninkijun,
            CASE 
                WHEN se.futan_juryo IS NULL OR se.futan_juryo = '' THEN '000'
                ELSE LPAD(se.futan_juryo::text, 3, '0')
            END as futan_juryo,
            CASE 
                WHEN se.bataiju IS NULL OR se.bataiju = '' THEN '000'
                ELSE LPAD(se.bataiju::text, 3, '0')
            END as bataiju,
            CASE 
                WHEN se.zogen_fugo = '-' THEN '-' || LPAD(COALESCE(se.zogen_sa::text, '00'), 2, '0')
                WHEN se.zogen_sa IS NULL OR se.zogen_sa = '' THEN '+00'
                ELSE '+' || LPAD(se.zogen_sa::text, 2, '0')
            END as zogen_sa,
            COALESCE(se.kishumei_ryakusho, '') as kishumei_ryakusho,
            COALESCE(se.chokyoshimei_ryakusho, '') as chokyoshimei_ryakusho,
            CASE 
                WHEN se.corner_1 IS NULL OR se.corner_1 = '' THEN '00'
                ELSE LPAD(se.corner_1::text, 2, '0')
            END as corner1_juni,
            CASE 
                WHEN se.corner_2 IS NULL OR se.corner_2 = '' THEN '00'
                ELSE LPAD(se.corner_2::text, 2, '0')
            END as corner2_juni,
            CASE 
                WHEN se.corner_3 IS NULL OR se.corner_3 = '' THEN '00'
                ELSE LPAD(se.corner_3::text, 2, '0')
            END as corner3_juni,
            CASE 
                WHEN se.corner_4 IS NULL OR se.corner_4 = '' THEN '00'
                ELSE LPAD(se.corner_4::text, 2, '0')
            END as corner4_juni,
            CASE 
                WHEN se.soha_time IS NULL OR se.soha_time = '' THEN '0000'
                ELSE LPAD(se.soha_time::text, 4, '0')
            END as soha_time,
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
                WHEN se.time_sa LIKE '+%%' THEN se.time_sa
                WHEN se.time_sa LIKE '-%%' THEN se.time_sa
                WHEN se.time_sa IS NULL OR se.time_sa = '' THEN '+000'
                ELSE '+' || LPAD(se.time_sa::text, 3, '0')
            END as time_sa,
            CASE 
                WHEN ra.kyori IS NULL THEN '0000'
                ELSE LPAD(ra.kyori::text, 4, '0')
            END as kyori,
            COALESCE(ra.track_code, '00') as track_code,
            COALESCE(ra.babajotai_code_shiba, '0') as shiba_babajotai_code,
            COALESCE(ra.babajotai_code_dirt, '0') as dirt_babajotai_code,
            COALESCE(ra.tenko_code, '0') as tenko_code,
            COALESCE(ra.kyosomei_hondai, '') as kyosomei_hondai,
            COALESCE(ra.grade_code, '') as grade_code,
            CASE
                WHEN se.kohan_3f IS NULL OR se.kohan_3f = '' THEN ''
                ELSE LPAD(se.kohan_3f::text, 3, '0')
            END as kohan_3f,
            CASE
                WHEN ra.zenhan_3f IS NULL OR ra.zenhan_3f = '' THEN ''
                ELSE LPAD(ra.zenhan_3f::text, 3, '0')
            END as zenhan_3f,
            CASE
                WHEN ra.kohan_3f IS NULL OR ra.kohan_3f = '' THEN ''
                ELSE LPAD(ra.kohan_3f::text, 3, '0')
            END as race_kohan_3f,
            COALESCE(se.dochaku_tosu, '0') as dochaku_tosu,
            LPAD(se.umaban::text, 2, '0') as umaban,
            CASE
                WHEN se.wakuban IS NULL OR se.wakuban = '' THEN '0'
                ELSE LPAD(se.wakuban::text, 1, '0')
            END as wakuban,
            COALESCE(um.ketto_joho_01b, '') as sire,
            '' as dam,
            COALESCE(um.ketto_joho_02b, '') as broodmare_sire,
            se.keibajo_code as keibajo_code_raw
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
            AND se.ketto_toroku_bango != '0000000000'
            AND se.kakutei_chakujun IS NOT NULL
            AND se.kakutei_chakujun != '00'
            AND se.bamei IS NOT NULL
            AND se.bamei != ''
        ORDER BY se.bamei, se.kaisai_tsukihi DESC
        """
        
        print("🔍 指定期間のレースデータ取得中...")
        cur.execute(query, (START_DATE, END_DATE))
        
        # カラム名定義（38項目+α）
        col_names = [
            "BAMEI", "RACE_CODE", "KAISAI_NEN", "KAISAI_GAPPI", "KAKUTEI_CHAKUJUN",
            "TANSHO_ODDS", "TANSHO_NINKIJUN", "FUTAN_JURYO", "BATAIJU", "ZOGEN_SA",
            "KISHUMEI_RYAKUSHO", "CHOKYOSHIMEI_RYAKUSHO", "CORNER1_JUNI", "CORNER2_JUNI",
            "CORNER3_JUNI", "CORNER4_JUNI", "SOHA_TIME", "BAREI", "SEIBETSU_CODE",
            "KEIBAJO_CODE", "RACE_BANGO", "KETTO_TOROKU_BANGO", "TIME_SA", "KYORI",
            "TRACK_CODE", "SHIBA_BABAJOTAI_CODE", "DIRT_BABAJOTAI_CODE", "TENKO_CODE",
            "KYOSOMEI_HONDAI", "GRADE_CODE", "KOHAN_3F", "ZENHAN_3F", "RACE_KOHAN_3F",
            "DOCHAKU_TOSU", "UMABAN", "WAKUBAN",
            "sire", "dam", "broodmare_sire", "track_name"
        ]
        
        # 5. 新レースデータを処理
        new_races = 0
        updated_horses = 0
        corner_fallback_count = 0

        for row in cur:
            horse_name = row[0].strip()
            
            # 競馬場名を設定
            keibajo_code = row[39]  # keibajo_code_raw
            track_name = KEIBAJO_MAP.get(keibajo_code, keibajo_code)
            
            # レースデータを構築
            race_data = dict(zip(col_names[:-1], row[:-1]))
            race_data['track_name'] = track_name
            
            # 血統情報をトリム
            if race_data['sire']:
                race_data['sire'] = race_data['sire'].strip()
            if race_data['broodmare_sire']:
                race_data['broodmare_sire'] = race_data['broodmare_sire'].strip()

            original_corners = [
                race_data.get('CORNER1_JUNI'),
                race_data.get('CORNER2_JUNI'),
                race_data.get('CORNER3_JUNI'),
                race_data.get('CORNER4_JUNI')
            ]
            filled_corners, fallback_used = fill_corner_values(original_corners)

            race_data['CORNER1_JUNI'] = filled_corners[0]
            race_data['CORNER2_JUNI'] = filled_corners[1]
            race_data['CORNER3_JUNI'] = filled_corners[2]
            race_data['CORNER4_JUNI'] = filled_corners[3]

            if fallback_used:
                corner_fallback_count += 1
            
            # 馬のデータを更新
            if horse_name not in horses_data:
                horses_data[horse_name] = {
                    "horse_name": horse_name,
                    "total_races": 0,
                    "races": [],
                    "last_update": datetime.now().isoformat()
                }
                updated_horses += 1
            
            # 重複チェック: 同じRACE_CODEが既に存在するか確認
            race_code = race_data['RACE_CODE']
            existing_race_codes = [r.get('RACE_CODE') for r in horses_data[horse_name]["races"]]
            
            if race_code not in existing_race_codes:
                # 新レースを先頭に追加
                horses_data[horse_name]["races"].insert(0, race_data)
                new_races += 1
                
                # 9走を超える場合は最古を削除
                if len(horses_data[horse_name]["races"]) > 9:
                    horses_data[horse_name]["races"] = horses_data[horse_name]["races"][:9]
                
                # total_racesとlast_updateを更新
                horses_data[horse_name]["total_races"] = len(horses_data[horse_name]["races"])
                horses_data[horse_name]["last_update"] = datetime.now().isoformat()
        
        print(f"\n📊 更新結果:")
        print(f"  新規レース: {new_races}件")
        print(f"  更新された馬: {updated_horses}頭")
        print(f"  総馬数: {len(horses_data)}頭")
        print(f"  コーナー補完適用レース: {corner_fallback_count}")
        
        # 6. 更新済みファイルを保存（metadataを含む）
        today = datetime.now().strftime("%Y%m%d")
        output_file = f"unified_knowledge_{today}.json"
        
        # metadataを作成
        metadata = {
            "version": "3.0",
            "created_at": datetime.now().isoformat(),
            "total_horses": len(horses_data),
            "data_period": f"None-{datetime.now().year}",
            "sdk_version": "JRA_SDK_V2",
            "engines": {
                "D-Logic": {
                    "description": "標準12項目分析",
                    "required_fields": [
                        "KAKUTEI_CHAKUJUN", "TANSHO_NINKIJUN", "KISHUMEI_RYAKUSHO",
                        "CHOKYOSHIMEI_RYAKUSHO", "FUTAN_JURYO", "BATAIJU",
                        "CORNER1_JUNI", "CORNER2_JUNI", "CORNER3_JUNI", "CORNER4_JUNI",
                        "SOHA_TIME", "KYORI", "TRACK_CODE", "TENKO_CODE"
                    ]
                },
                "I-Logic": {
                    "description": "拡張分析（血統含む）",
                    "required_fields": ["sire", "broodmare_sire", "KYOSOMEI_HONDAI", "GRADE_CODE"]
                },
                "IMLogic": {
                    "description": "拡張分析（血統含む）",
                    "required_fields": ["sire", "broodmare_sire", "KYOSOMEI_HONDAI", "GRADE_CODE"]
                },
                "ViewLogic": {
                    "description": "展開予想分析",
                    "required_fields": [
                        "KAKUTEI_CHAKUJUN", "KEIBAJO_CODE", "KYORI",
                        "KOHAN_3F", "DOCHAKU_TOSU", "ZENHAN_3F", "RACE_KOHAN_3F"
                    ]
                },
                "ViewLogic過去データ": {
                    "description": "必須8フィールド",
                    "required_fields": [
                        "KAKUTEI_CHAKUJUN", "KEIBAJO_CODE", "KYORI", "RACE_BANGO",
                        "UMABAN", "WAKUBAN", "KISHUMEI_RYAKUSHO", "TANSHO_NINKIJUN"
                    ]
                }
            }
        }
        
        # metadataとhorsesを含む完全な構造を作成
        full_data = {
            "metadata": metadata,
            "horses": horses_data
        }
        
        print(f"\n💾 ファイル保存中: {output_file}")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(full_data, f, ensure_ascii=False, indent=2)
        
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
        print(f"✅ 総馬数: {len(horses_data)}")
        print("\n次のステップ:")
        print("1. ローカルでバックエンドテスト")
        print("2. テスト成功後、Cloudflareにアップロード")
        print("3. 騎手ナレッジファイルも同様に更新")
        
        return output_file
        
    except Exception as e:
        import traceback
        print(f"\n❌ エラー: {e}")
        print(f"詳細: {traceback.format_exc()}")
        return None

def main():
    """メイン処理"""
    print("🏇 JRA一括更新処理開始")
    print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 統合ナレッジファイル更新
    result = update_unified_knowledge()
    
    if result:
        print("\n✅ すべての処理が正常に完了しました")
        return result
    else:
        print("\n❌ 更新処理に失敗しました")
        return None

if __name__ == "__main__":
    main()
