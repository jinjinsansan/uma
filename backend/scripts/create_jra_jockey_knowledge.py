#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JRA騎手ナレッジファイル全件作成スクリプト
- JRA全10場対応
- 騎手×会場×距離、馬場状態、枠番、種牡馬の成績集計
- 毎週フル再構築用（weekly_knowledge_update.pyから呼ばれる）
"""

import psycopg2
import json
import sys
import io
import os
from datetime import datetime, timedelta
from collections import defaultdict
import traceback

# Windows環境での文字化け対策
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# =============================================================================
# 設定
# =============================================================================

CONNECTION_PARAMS = {
    "host": "127.0.0.1",
    "port": "5432",
    "database": "pckeiba",
    "user": "postgres",
    "password": "postgres"
}

KEIBAJO_MAP = {
    # JRA 国内
    '01': '札幌', '02': '函館', '03': '福島', '04': '新潟',
    '05': '東京', '06': '中山', '07': '中京', '08': '京都',
    '09': '阪神', '10': '小倉',
    # 海外
    'A4': 'アメリカ',
    'A6': 'イギリス(アスコット等)',
    'A8': 'イギリス(ニューマーケット等)',
    'B2': 'アイルランド',
    'B6': 'オーストラリア',
    'B8': 'カナダ',
    'C0': 'イタリア',
    'C2': 'ドイツ',
    'C7': 'UAE(ドバイ)',
    'F0': '韓国',
    'G0': '香港',
    'K6': 'サウジアラビア',
    'M8': 'カタール',
    'N2': 'バーレーン',
}


def calculate_date_range():
    """実行日から6年前までの年リストを計算"""
    today = datetime.now()
    years_back = today - timedelta(days=6 * 365)
    years = tuple(str(y) for y in range(years_back.year, today.year + 1))
    return years


def fetch_jockey_data(years):
    """データベースからJRA騎手成績データを取得して集計"""

    print("\nデータベース接続中...")
    conn = psycopg2.connect(**CONNECTION_PARAMS)
    cur = conn.cursor()
    print("  接続成功")

    jra_codes = tuple(KEIBAJO_MAP.keys())

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
    FROM jvd_se se
    JOIN jvd_ra ra ON (
        se.kaisai_nen = ra.kaisai_nen
        AND se.kaisai_tsukihi = ra.kaisai_tsukihi
        AND se.keibajo_code = ra.keibajo_code
        AND se.race_bango = ra.race_bango
    )
    LEFT JOIN jvd_um nu ON se.ketto_toroku_bango = nu.ketto_toroku_bango
    WHERE se.kaisai_nen IN %s
        AND se.keibajo_code IN %s
        AND se.kishumei_ryakusho IS NOT NULL
        AND se.kishumei_ryakusho != ''
        AND se.kakutei_chakujun IS NOT NULL
        AND se.kakutei_chakujun != '00'
        AND se.ketto_toroku_bango != '0000000000'
    ORDER BY se.kishumei_ryakusho, se.kaisai_nen DESC, se.kaisai_tsukihi DESC
    """

    print(f"  対象年: {', '.join(years)}")
    print(f"  対象競馬場: JRA国内{sum(1 for c in jra_codes if not c[0].isalpha())}場 + 海外{sum(1 for c in jra_codes if c[0].isalpha())}場")
    print(f"  データ取得中...")
    cur.execute(query, (years, jra_codes))

    jockey_data = {}
    row_count = 0

    for row in cur:
        row_count += 1
        if row_count % 100000 == 0:
            print(f"    {row_count:,}件処理... ({len(jockey_data):,}名)")

        jockey_name = row[0].strip()
        keibajo_code = row[3]
        kyori = row[4]
        track_code = row[5]
        baba_code = row[6]
        wakuban = row[7] if row[7] else '0'
        bamei = row[8].strip() if row[8] else ''
        chakujun = row[9]
        tosuu = row[10]
        sire = row[11].strip() if row[11] else ''
        kaisai_nen = row[1]
        kaisai_tsukihi = row[2]

        if not jockey_name:
            continue

        keibajo_name = KEIBAJO_MAP.get(keibajo_code, keibajo_code)

        # 騎手データ初期化
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

        position = int(chakujun) if chakujun and str(chakujun).strip().isdigit() else 99
        total_horses = int(tosuu) if tosuu and str(tosuu).strip().isdigit() else 18
        is_fukusho = 0 < position <= 3

        result_data = {
            "date": kaisai_nen + "-" + kaisai_tsukihi,
            "horse_name": bamei,
            "position": position,
            "total_horses": total_horses,
            "is_fukusho": is_fukusho
        }

        # 1. venue_course_stats
        venue_key = f"{keibajo_name}_{kyori}m"
        if venue_key not in jockey_data[jockey_name]["venue_course_stats"]:
            jockey_data[jockey_name]["venue_course_stats"][venue_key] = {
                "results": [], "fukusho_rate": 0.0, "race_count": 0
            }
        stats = jockey_data[jockey_name]["venue_course_stats"][venue_key]
        stats["results"].append(result_data)
        stats["race_count"] += 1

        # 2. track_condition_stats
        track_label = '芝' if track_code == '17' else 'ダート'
        track_key = f"{track_label}({baba_code})"
        if track_key not in jockey_data[jockey_name]["track_condition_stats"]:
            jockey_data[jockey_name]["track_condition_stats"][track_key] = {
                "results": [], "fukusho_rate": 0.0, "race_count": 0
            }
        stats = jockey_data[jockey_name]["track_condition_stats"][track_key]
        stats["results"].append(result_data)
        stats["race_count"] += 1

        # 3. post_position_stats
        post_key = f"枠{wakuban}"
        if post_key not in jockey_data[jockey_name]["post_position_stats"]:
            jockey_data[jockey_name]["post_position_stats"][post_key] = {
                "results": [], "fukusho_rate": 0.0, "race_count": 0
            }
        stats = jockey_data[jockey_name]["post_position_stats"][post_key]
        stats["results"].append(result_data)
        stats["race_count"] += 1

        # 4. sire_stats
        if sire:
            if sire not in jockey_data[jockey_name]["sire_stats"]:
                jockey_data[jockey_name]["sire_stats"][sire] = {
                    "results": [], "fukusho_rate": 0.0, "race_count": 0
                }
            stats = jockey_data[jockey_name]["sire_stats"][sire]
            stats["results"].append(result_data)
            stats["race_count"] += 1

        jockey_data[jockey_name]["overall_stats"]["total_races_analyzed"] += 1

    cur.close()
    conn.close()

    print(f"\n  処理完了:")
    print(f"    総レコード: {row_count:,}")
    print(f"    騎手数: {len(jockey_data):,}")

    return jockey_data, row_count


def calculate_fukusho_rates(jockey_data):
    """全騎手の複勝率を計算"""
    print("\n複勝率計算中...")
    for jockey in jockey_data.values():
        for category in ["venue_course_stats", "track_condition_stats",
                         "post_position_stats", "sire_stats"]:
            for stats in jockey[category].values():
                if stats["race_count"] > 0:
                    fukusho_count = sum(1 for r in stats["results"] if r["is_fukusho"])
                    stats["fukusho_rate"] = round((fukusho_count / stats["race_count"]) * 100, 1)

        total_races = jockey["overall_stats"]["total_races_analyzed"]
        if total_races > 0:
            total_fukusho = sum(
                1 for r in
                [r for s in jockey["venue_course_stats"].values() for r in s["results"]]
                if r["is_fukusho"]
            )
            jockey["overall_stats"]["overall_fukusho_rate"] = round(
                (total_fukusho / total_races) * 100, 1
            )
    print("  完了")


def main():
    print("=" * 70)
    print("JRA騎手ナレッジファイル作成")
    print("=" * 70)
    print(f"実行: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    years = calculate_date_range()
    print(f"対象: {len(years)}年分 ({years[0]}~{years[-1]})")

    try:
        jockey_data, total_records = fetch_jockey_data(years)
        if not jockey_data:
            print("データ取得失敗")
            return False

        calculate_fukusho_rates(jockey_data)

        # 保存
        timestamp = datetime.now().strftime('%Y%m%d')
        output_file = f'jra_jockey_knowledge_{timestamp}.json'

        output = {
            "metadata": {
                "version": "2.0",
                "type": "jra_jockey",
                "created_at": datetime.now().isoformat(),
                "total_jockeys": len(jockey_data),
                "total_records": total_records,
                "target_venues": KEIBAJO_MAP,
            },
            "jockeys": jockey_data
        }

        print(f"\n保存中: {output_file}")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False)

        file_size = os.path.getsize(output_file) / (1024 * 1024)
        print(f"  サイズ: {file_size:.1f} MB")
        print(f"  騎手数: {len(jockey_data):,}")

        # TOP20
        top = sorted(
            [(n, j["overall_stats"]["total_races_analyzed"]) for n, j in jockey_data.items()],
            key=lambda x: -x[1]
        )[:20]
        print(f"\n  騎乗数 TOP20:")
        for name, count in top:
            rate = jockey_data[name]["overall_stats"]["overall_fukusho_rate"]
            print(f"    {name}: {count:,}騎乗 (複勝率{rate}%)")

        print("\n" + "=" * 70)
        print("完了!")
        print("=" * 70)
        return True

    except Exception as e:
        print(f"\nエラー: {e}")
        print(traceback.format_exc())
        return False


if __name__ == "__main__":
    main()
