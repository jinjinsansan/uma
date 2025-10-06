#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
地方競馬版（南関東）馬ナレッジファイル週次差分更新スクリプト
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

# 公式重賞レース辞書
FIXED_GRADED_RACES = {
    '東京大賞典': {'venue_code': '42', 'venue_name': '大井'},
    '帝王賞': {'venue_code': '42', 'venue_name': '大井'},
    '川崎記念': {'venue_code': '43', 'venue_name': '川崎'},
    'かしわ記念': {'venue_code': '44', 'venue_name': '船橋'},
    '浦和記念': {'venue_code': '45', 'venue_name': '浦和'},
    'ジャパンダートダービー': {'venue_code': '42', 'venue_name': '大井'},
    '羽田盃': {'venue_code': '42', 'venue_name': '大井'},
    '東京スプリント': {'venue_code': '42', 'venue_name': '大井'},
    'エンプレス杯': {'venue_code': '43', 'venue_name': '川崎'},
    '関東オークス': {'venue_code': '43', 'venue_name': '川崎'},
    'クイーン賞': {'venue_code': '44', 'venue_name': '船橋'},
    'マリーンカップ': {'venue_code': '44', 'venue_name': '船橋'}
}

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

def correct_venue_perfect(kaisai_nen, kaisai_gappi, original_code, race_name=None, schedule_master=None):
    """
    完全な会場補正（4段階）
    """
    race_date = f"{kaisai_nen}{kaisai_gappi}"

    # 1. 公式重賞レースチェック
    if race_name:
        for graded_name, venue_info in FIXED_GRADED_RACES.items():
            if graded_name in race_name:
                return venue_info['venue_code'], venue_info['venue_name'], True

    # 2. スケジュールマスター照合（最重要）
    if schedule_master and race_date in schedule_master:
        venues = schedule_master[race_date]
        if venues and len(venues) > 0:
            corrected_code = venues[0]
            return corrected_code, NANKAN_CODES.get(corrected_code, f'不明({corrected_code})'), True

    # 3. パターンマッチング
    if race_name:
        if '東京' in race_name or '大井' in race_name or 'TCK' in race_name:
            return '42', '大井', True
        elif '川崎' in race_name or 'スパーキング' in race_name:
            return '43', '川崎', True
        elif '船橋' in race_name or 'マリーン' in race_name:
            return '44', '船橋', True
        elif '浦和' in race_name or 'さきたま' in race_name:
            return '45', '浦和', True

    # 補正できない場合は元のコードを返す
    return original_code, NANKAN_CODES.get(original_code, f'不明({original_code})'), False

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

def download_existing_knowledge():
    """既存のナレッジファイルをCloudflareからダウンロード"""
    print("📥 既存ナレッジファイルをダウンロード中...")
    
    # CDN URLを指定
    url = "https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/nankan_unified_knowledge_20250907.json"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        full_data = response.json()
        horses_data = full_data.get("horses", full_data)
        print(f"✅ {len(horses_data)}頭のデータをダウンロード完了")
        return horses_data
    except Exception as e:
        print(f"⚠️ ダウンロードエラー: {e}")
        print("空のデータから開始します")
        return {}

def update_unified_knowledge():
    """統合ナレッジファイルを週末データで更新"""
    
    print("=" * 80)
    print("🏇 地方競馬版（南関東）馬ナレッジファイル週次更新")
    print("=" * 80)
    
    try:
        # 1. 既存データをダウンロード
        horses_data = download_existing_knowledge()
        
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
        
        # 5. 週末の新レースデータを取得
        query = """
        SELECT
            se.bamei as "BAMEI",
            se.kaisai_nen || se.kaisai_tsukihi || se.keibajo_code ||
                LPAD(se.race_bango::text, 2, '0') || '00' as "RACE_CODE",
            se.kaisai_nen as "KAISAI_NEN",
            se.kaisai_tsukihi as "KAISAI_GAPPI",
            LPAD(COALESCE(se.kakutei_chakujun, '00'), 2, '0') as "KAKUTEI_CHAKUJUN",
            LPAD(COALESCE(se.tansho_odds::text, '0000'), 4, '0') as "TANSHO_ODDS",
            LPAD(COALESCE(se.tansho_ninkijun, '00'), 2, '0') as "TANSHO_NINKIJUN",
            LPAD(COALESCE(se.futan_juryo::text, '000'), 3, '0') as "FUTAN_JURYO",
            LPAD(COALESCE(se.bataiju::text, '000'), 3, '0') as "BATAIJU",
            CASE
                WHEN se.zogen_fugo = '-' THEN '-' || LPAD(COALESCE(se.zogen_sa::text, '000'), 3, '0')
                ELSE '+' || LPAD(COALESCE(se.zogen_sa::text, '000'), 3, '0')
            END as "ZOGEN_SA",
            COALESCE(se.kishumei_ryakusho, '') as "KISHUMEI_RYAKUSHO",
            COALESCE(se.chokyoshimei_ryakusho, '') as "CHOKYOSHIMEI_RYAKUSHO",
            LPAD(COALESCE(se.corner_1, '00'), 2, '0') as "CORNER1_JUNI",
            LPAD(COALESCE(se.corner_2, '00'), 2, '0') as "CORNER2_JUNI",
            LPAD(COALESCE(se.corner_3, '00'), 2, '0') as "CORNER3_JUNI",
            LPAD(COALESCE(se.corner_4, '00'), 2, '0') as "CORNER4_JUNI",
            COALESCE(se.soha_time, '0000') as "SOHA_TIME",
            COALESCE(nu.seibetsu_code, '0') as "SEIBETSU_CODE",
            CASE
                WHEN nu.seinengappi IS NOT NULL AND nu.seinengappi != '' THEN
                    LPAD(GREATEST(0, (se.kaisai_nen::int - SUBSTRING(nu.seinengappi, 1, 4)::int))::text, 2, '0')
                ELSE '00'
            END as "BAREI",
            se.keibajo_code as "KEIBAJO_CODE",
            LPAD(se.race_bango::text, 2, '0') as "RACE_BANGO",
            se.ketto_toroku_bango as "KETTO_TOROKU_BANGO",
            CASE
                WHEN se.time_sa LIKE '+%%' THEN se.time_sa
                WHEN se.time_sa LIKE '-%%' THEN se.time_sa
                ELSE '+' || LPAD(COALESCE(se.time_sa, '000'), 3, '0')
            END as "TIME_SA",
            LPAD(COALESCE(ra.kyori::text, '0000'), 4, '0') as "KYORI",
            COALESCE(ra.track_code, '00') as "TRACK_CODE",
            COALESCE(ra.babajotai_code_shiba, '0') as "SHIBA_BABAJOTAI_CODE",
            COALESCE(ra.babajotai_code_dirt, '0') as "DIRT_BABAJOTAI_CODE",
            COALESCE(ra.tenko_code, '0') as "TENKO_CODE",
            COALESCE(ra.kyosomei_hondai, '') as "KYOSOMEI_HONDAI",
            COALESCE(ra.grade_code, '  ') as "GRADE_CODE",
            COALESCE(se.kohan_3f, '000') as "KOHAN_3F",
            COALESCE(ra.zenhan_3f, '000') as "ZENHAN_3F",
            COALESCE(ra.kohan_3f, '000') as "RACE_KOHAN_3F",
            COALESCE(se.dochaku_tosu, '0') as "DOCHAKU_TOSU",
            LPAD(COALESCE(se.umaban::text, '00'), 2, '0') as "UMABAN",
            LPAD(COALESCE(se.wakuban::text, '0'), 1, '0') as "WAKUBAN",
            COALESCE(nu.ketto_joho_01b, '') as "sire",
            '' as "dam",
            COALESCE(nu.ketto_joho_03b, '') as "broodmare_sire"
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
            AND se.ketto_toroku_bango IS NOT NULL
            AND se.ketto_toroku_bango != ''
            AND se.kakutei_chakujun IS NOT NULL
            AND se.kakutei_chakujun != '00'
            AND se.bamei IS NOT NULL
            AND se.bamei != ''
        ORDER BY se.bamei, se.kaisai_tsukihi DESC
        """
        
        print("🔍 週末のレースデータ取得中...")
        cur.execute(query, (year, saturday, sunday))
        
        # カラム名定義
        col_names = [
            "BAMEI", "RACE_CODE", "KAISAI_NEN", "KAISAI_GAPPI", "KAKUTEI_CHAKUJUN",
            "TANSHO_ODDS", "TANSHO_NINKIJUN", "FUTAN_JURYO", "BATAIJU", "ZOGEN_SA",
            "KISHUMEI_RYAKUSHO", "CHOKYOSHIMEI_RYAKUSHO", "CORNER1_JUNI", "CORNER2_JUNI",
            "CORNER3_JUNI", "CORNER4_JUNI", "SOHA_TIME", "SEIBETSU_CODE", "BAREI",
            "KEIBAJO_CODE", "RACE_BANGO", "KETTO_TOROKU_BANGO", "TIME_SA", "KYORI",
            "TRACK_CODE", "SHIBA_BABAJOTAI_CODE", "DIRT_BABAJOTAI_CODE", "TENKO_CODE",
            "KYOSOMEI_HONDAI", "GRADE_CODE", "KOHAN_3F", "ZENHAN_3F", "RACE_KOHAN_3F",
            "DOCHAKU_TOSU", "UMABAN", "WAKUBAN",
            "sire", "dam", "broodmare_sire"
        ]
        
        # 6. 新レースデータを処理
        new_races = 0
        updated_horses = 0
        corner_fallback_count = 0
        corrected_venues = 0
        
        for row in cur:
            horse_name = row[0].strip()
            kaisai_nen = row[2]
            kaisai_gappi = row[3]
            original_code = row[19]
            race_name = row[28]
            
            # 会場補正
            corrected_code, venue_name, was_corrected = correct_venue_perfect(
                kaisai_nen, kaisai_gappi, original_code, race_name, schedule_master
            )
            if was_corrected:
                corrected_venues += 1
            
            # レースデータを構築
            race_data = dict(zip(col_names, row))
            race_data['KEIBAJO_CODE'] = corrected_code
            race_data['track_name'] = venue_name
            
            # 血統情報をトリム
            if race_data['sire']:
                race_data['sire'] = race_data['sire'].strip()
            if race_data['broodmare_sire']:
                race_data['broodmare_sire'] = race_data['broodmare_sire'].strip()

            # コーナー補完
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
        print(f"  会場補正適用: {corrected_venues}件")
        print(f"  コーナー補完適用レース: {corner_fallback_count}")
        
        # 7. 更新済みファイルを保存
        output_file = "nankan_unified_knowledge_20250907.json"
        
        # metadataを作成
        metadata = {
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "total_horses": len(horses_data),
            "data_period": f"None-{datetime.now().year}",
            "sdk_version": "NAR_SDK_V1"
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
        print("🎉 週次更新完了!")
        print("=" * 80)
        print(f"✅ 出力ファイル: {output_file}")
        print(f"✅ 新規レース数: {new_races}")
        print(f"✅ 総馬数: {len(horses_data)}")
        print(f"✅ 会場補正率: {(corrected_venues/new_races*100):.1f}%" if new_races > 0 else "")
        print("\n次のステップ:")
        print("1. ファイル名を nar_unified_knowledge.json に変更")
        print("2. このファイルをCloudflareにアップロード")
        
        return output_file
        
    except Exception as e:
        import traceback
        print(f"\n❌ エラー: {e}")
        print(f"詳細: {traceback.format_exc()}")
        return None

def main():
    """メイン処理"""
    print("🏇 地方競馬版（南関東）週次更新処理開始")
    print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 統合ナレッジファイル更新
    result = update_unified_knowledge()
    
    if result:
        print("\n✅ すべての処理が正常に完了しました")
    else:
        print("\n❌ 更新処理に失敗しました")

if __name__ == "__main__":
    main()
