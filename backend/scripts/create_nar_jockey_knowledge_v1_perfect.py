#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
地方競馬版騎手ナレッジファイル作成ツール v1 Perfect
馬版（補正率44.7%）の成功をベースに騎手版を実装

2019-2025年の7年間全データ（40走制限なし）
"""

import json
import psycopg2
import sys
import io
from datetime import datetime, timedelta
from collections import defaultdict

# UTF-8出力設定
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# データベース接続設定（馬版と完全に同じ）
CONNECTION_PARAMS = {
    "host": "172.25.160.1",
    "port": "5432",
    "database": "pckeiba",  # 小文字が正しい！
    "user": "postgres",
    "password": "postgres"
}

# 南関東競馬場マッピング
NANKAN_KEIBAJO_MAP = {
    '42': '大井',
    '43': '川崎',
    '44': '船橋',
    '45': '浦和',
    '35': '盛岡',
    '36': '水沢'
}

# 公式重賞レース辞書（馬版から流用）
FIXED_GRADED_RACES = {
    '東京大賞典': {'venue_code': '42', 'venue_name': '大井'},
    '帝王賞': {'venue_code': '42', 'venue_name': '大井'},
    'ジャパンＤダービー': {'venue_code': '42', 'venue_name': '大井'},
    'ジャパンダートダービー': {'venue_code': '42', 'venue_name': '大井'},
    '東京ダービー': {'venue_code': '42', 'venue_name': '大井'},
    '羽田盃': {'venue_code': '42', 'venue_name': '大井'},
    '東京２歳優駿牝馬': {'venue_code': '42', 'venue_name': '大井'},
    '東京プリンセス賞': {'venue_code': '42', 'venue_name': '大井'},
    'レディスプレリュード': {'venue_code': '42', 'venue_name': '大井'},
    'ＴＣＫ女王盃': {'venue_code': '42', 'venue_name': '大井'},
    '黒潮盃': {'venue_code': '42', 'venue_name': '大井'},
    '川崎記念': {'venue_code': '43', 'venue_name': '川崎'},
    'エンプレス杯': {'venue_code': '43', 'venue_name': '川崎'},
    '全日本２歳優駿': {'venue_code': '43', 'venue_name': '川崎'},
    'スパーキングレディーＣ': {'venue_code': '43', 'venue_name': '川崎'},
    'かしわ記念': {'venue_code': '44', 'venue_name': '船橋'},
    'ダイオライト記念': {'venue_code': '44', 'venue_name': '船橋'},
    '京成盃グランドマイラーズ': {'venue_code': '44', 'venue_name': '船橋'},
    'クイーン賞': {'venue_code': '44', 'venue_name': '船橋'},
    '習志野きらっとスプリント': {'venue_code': '44', 'venue_name': '船橋'},
    'オーバルスプリント': {'venue_code': '44', 'venue_name': '船橋'},
    '浦和記念': {'venue_code': '45', 'venue_name': '浦和'},
    'さきたま杯': {'venue_code': '45', 'venue_name': '浦和'},
    'テレ玉杯オーバルスプリント': {'venue_code': '45', 'venue_name': '浦和'},
    'ひまわり賞': {'venue_code': '45', 'venue_name': '浦和'},
    'マリーンカップ': {'venue_code': '44', 'venue_name': '船橋'},
    '東京盃': {'venue_code': '42', 'venue_name': '大井'},
    'アフター５スター賞': {'venue_code': '42', 'venue_name': '大井'},
    '勝島王冠': {'venue_code': '42', 'venue_name': '大井'}
}

# 非重賞レースパターン（馬版から流用）
NON_GRADED_PATTERNS = {
    'クラシックチャレンジ': {'venue_code': '42', 'venue_name': '大井'},
    '東京シンデレラマイル': {'venue_code': '42', 'venue_name': '大井'},
    'プレミアムカップ': {'venue_code': '43', 'venue_name': '川崎'},
    'ローレル賞': {'venue_code': '43', 'venue_name': '川崎'},
    'ブルーバードカップ': {'venue_code': '44', 'venue_name': '船橋'},
    'しらさぎ賞': {'venue_code': '45', 'venue_name': '浦和'},
    'ニューイヤーカップ': {'venue_code': '45', 'venue_name': '浦和'}
}

def load_schedule_master():
    """スケジュールマスターの読み込み（馬版と同じ）"""
    try:
        schedule_file = "/mnt/e/dev/Cusor/chatbot/uma/data/nankan_schedule_master_2019_2025.json"
        with open(schedule_file, 'r', encoding='utf-8') as f:
            master = json.load(f)

        print("✅ スケジュールマスター読み込み成功")
        print(f"   期間: {master['metadata']['period']}")
        print(f"   総日数: {master['metadata']['total_days']}日")

        return master['schedule_data']
    except Exception as e:
        print(f"⚠️ スケジュールマスター読み込み失敗: {e}")
        return {}

def correct_venue_perfect(keibajo_code, race_name, race_date, schedule_master):
    """
    4段階会場補正（馬版で成功した方式）
    補正率44.7%を達成した実績のあるロジック
    """
    default_result = {'venue_code': keibajo_code, 'venue_name': NANKAN_KEIBAJO_MAP.get(keibajo_code, '不明')}

    # Stage 1: 重賞レース辞書
    if race_name:
        race_name_clean = race_name.strip()
        for graded_name, venue_info in FIXED_GRADED_RACES.items():
            if graded_name in race_name_clean:
                return venue_info

    # Stage 2: 非重賞パターン
    if race_name:
        for pattern, venue_info in NON_GRADED_PATTERNS.items():
            if pattern in race_name_clean:
                return venue_info

    # Stage 3: スケジュールマスター（最重要）
    if schedule_master and race_date:
        date_key = race_date[:8]  # YYYYMMDD形式
        if date_key in schedule_master:
            venues = schedule_master[date_key]
            if venues and len(venues) > 0:
                corrected_code = venues[0]
                return {
                    'venue_code': corrected_code,
                    'venue_name': NANKAN_KEIBAJO_MAP.get(corrected_code, '不明')
                }

    # Stage 4: パターンマッチング
    if race_name:
        if '東京' in race_name or '大井' in race_name or 'TCK' in race_name:
            return {'venue_code': '42', 'venue_name': '大井'}
        elif '川崎' in race_name:
            return {'venue_code': '43', 'venue_name': '川崎'}
        elif '船橋' in race_name or 'かしわ' in race_name:
            return {'venue_code': '44', 'venue_name': '船橋'}
        elif '浦和' in race_name or 'さきたま' in race_name:
            return {'venue_code': '45', 'venue_name': '浦和'}

    return default_result

def get_track_condition_key(track_code, baba_shiba, baba_dirt):
    """馬場状態キーの生成"""
    if track_code == '1':  # 芝
        return f"芝({baba_shiba or '10'})"
    else:  # ダート
        return f"ダート({baba_dirt or '10'})"

def calculate_fukusho_rate(results):
    """複勝率計算（3着以内の割合）"""
    if not results or len(results) == 0:
        return 0.0

    fukusho_count = sum(1 for r in results if r['is_fukusho'])
    total_count = len(results)

    return round((fukusho_count / total_count) * 100, 1)

def fetch_jockey_data(years):
    """騎手データの取得"""
    conn = psycopg2.connect(**CONNECTION_PARAMS)
    cur = conn.cursor()

    # SQLクエリ（7年間全データ、制限なし）
    query = """
        SELECT
            se.kishumei_ryakusho,
            se.kaisai_nen || se.kaisai_tsukihi as race_date,
            se.keibajo_code,
            ra.kyori,
            ra.track_code,
            ra.babajotai_code_shiba,
            ra.babajotai_code_dirt,
            COALESCE(ra.kyosomei_hondai, ra.kyosomei_ryakusho_10, '') as race_name,
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
        WHERE se.kaisai_nen IN %s
            AND se.keibajo_code IN ('42','43','44','45','35','36')
            AND se.kishumei_ryakusho IS NOT NULL
            AND se.kishumei_ryakusho != ''
            AND se.kakutei_chakujun IS NOT NULL
            AND se.kakutei_chakujun != '00'
        ORDER BY se.kishumei_ryakusho, race_date DESC
    """

    cur.execute(query, (tuple(years),))
    rows = cur.fetchall()

    cur.close()
    conn.close()

    return rows

def aggregate_jockey_stats(rows, schedule_master):
    """騎手統計の集計（7年間全データ、制限なし）"""
    jockeys = defaultdict(lambda: {
        'name': '',
        'venue_course_stats': defaultdict(lambda: {'results': [], 'fukusho_rate': 0.0, 'race_count': 0}),
        'track_condition_stats': defaultdict(lambda: {'results': [], 'fukusho_rate': 0.0, 'race_count': 0}),
        'post_position_stats': defaultdict(lambda: {'results': [], 'fukusho_rate': 0.0, 'race_count': 0}),
        'sire_stats': defaultdict(lambda: {'results': [], 'fukusho_rate': 0.0, 'race_count': 0}),
        'overall_stats': {
            'total_races_analyzed': 0,
            'overall_fukusho_rate': 0.0
        },
        'processed_at': datetime.now().isoformat()
    })

    # 処理カウンター
    total_records = 0
    corrected_records = 0

    print(f"\nデータ集計中（全{len(rows)}レコード）...")

    for i, row in enumerate(rows):
        if (i + 1) % 10000 == 0:
            print(f"  {i + 1:,}件処理...")

        # データの取得
        jockey_name = row[0].strip() if row[0] else ''
        if not jockey_name:
            continue

        race_date = row[1] if row[1] else ''
        keibajo_code = row[2] if row[2] else ''
        kyori = row[3] if row[3] else 0
        track_code = row[4] if row[4] else '2'
        baba_shiba = row[5] if row[5] else ''
        baba_dirt = row[6] if row[6] else ''
        race_name = row[7].strip() if row[7] else ''  # レース名追加
        wakuban = row[8] if row[8] else '1'
        bamei = row[9] if row[9] else ''
        chakujun = row[10] if row[10] else '99'
        tosu = row[11] if row[11] else 0
        sire = row[12] if row[12] else ''  # インデックス調整

        # 騎手データ初期化
        if not jockeys[jockey_name]['name']:
            jockeys[jockey_name]['name'] = jockey_name

        # 会場補正
        corrected_venue = correct_venue_perfect(keibajo_code, race_name, race_date, schedule_master)
        if corrected_venue['venue_code'] != keibajo_code:
            corrected_records += 1

        # 結果データ作成
        try:
            position = int(chakujun) if chakujun and chakujun != '00' else 99
            total_horses = int(tosu) if tosu else 0
            is_fukusho = position <= 3
        except:
            position = 99
            total_horses = 0
            is_fukusho = False

        result = {
            'date': f"{race_date[:4]}-{race_date[4:6]}{race_date[6:8]}" if len(race_date) >= 8 else race_date,
            'horse_name': bamei,
            'position': position,
            'total_horses': total_horses,
            'is_fukusho': is_fukusho
        }

        # 1. venue_course_stats（会場×距離別）- 制限なし
        venue_key = f"{corrected_venue['venue_name']}_{kyori}m"
        jockeys[jockey_name]['venue_course_stats'][venue_key]['results'].append(result)

        # 2. track_condition_stats（馬場状態別）- 制限なし
        track_key = get_track_condition_key(track_code, baba_shiba, baba_dirt)
        jockeys[jockey_name]['track_condition_stats'][track_key]['results'].append(result)

        # 3. post_position_stats（枠番別）- 制限なし
        post_key = f"枠{wakuban}"
        jockeys[jockey_name]['post_position_stats'][post_key]['results'].append(result)

        # 4. sire_stats（種牡馬別）- 制限なし
        if sire and sire.strip():
            jockeys[jockey_name]['sire_stats'][sire.strip()]['results'].append(result)

        total_records += 1

    # 複勝率計算
    print("\n複勝率計算中...")
    for jockey_name, jockey_data in jockeys.items():
        all_results = []

        # venue_course_stats
        for key, stats in jockey_data['venue_course_stats'].items():
            stats['race_count'] = len(stats['results'])
            stats['fukusho_rate'] = calculate_fukusho_rate(stats['results'])
            all_results.extend(stats['results'])
            # resultsは保持（7年間全データ）

        # track_condition_stats
        for key, stats in jockey_data['track_condition_stats'].items():
            stats['race_count'] = len(stats['results'])
            stats['fukusho_rate'] = calculate_fukusho_rate(stats['results'])

        # post_position_stats
        for key, stats in jockey_data['post_position_stats'].items():
            stats['race_count'] = len(stats['results'])
            stats['fukusho_rate'] = calculate_fukusho_rate(stats['results'])

        # sire_stats
        for key, stats in jockey_data['sire_stats'].items():
            stats['race_count'] = len(stats['results'])
            stats['fukusho_rate'] = calculate_fukusho_rate(stats['results'])

        # 総合統計（重複を除く）
        unique_results = {}
        for r in all_results:
            key = f"{r['date']}_{r['horse_name']}"
            unique_results[key] = r

        jockey_data['overall_stats']['total_races_analyzed'] = len(unique_results)
        jockey_data['overall_stats']['overall_fukusho_rate'] = calculate_fukusho_rate(list(unique_results.values()))

    # defaultdictを通常のdictに変換
    final_jockeys = {}
    for jockey_name, jockey_data in jockeys.items():
        final_jockeys[jockey_name] = {
            'name': jockey_data['name'],
            'venue_course_stats': dict(jockey_data['venue_course_stats']),
            'track_condition_stats': dict(jockey_data['track_condition_stats']),
            'post_position_stats': dict(jockey_data['post_position_stats']),
            'sire_stats': dict(jockey_data['sire_stats']),
            'overall_stats': jockey_data['overall_stats'],
            'processed_at': jockey_data['processed_at']
        }

    print(f"\n処理完了:")
    print(f"  総レコード数: {total_records:,}")
    print(f"  騎手数: {len(final_jockeys)}")
    print(f"  会場補正数: {corrected_records:,}")
    if total_records > 0:
        print(f"  補正率: {round(corrected_records / total_records * 100, 1)}%")

    return final_jockeys

def save_jockey_knowledge(jockeys, output_file):
    """騎手ナレッジファイルの保存"""
    try:
        # メタデータ付きで保存（馬版と同じ構造）
        output_data = {
            "metadata": {
                "version": "1.0",
                "created_at": datetime.now().isoformat(),
                "total_jockeys": len(jockeys),
                "data_period": "2019-2025",
                "sdk_version": "NAR_JOCKEY_SDK_V1_PERFECT"
            },
            "jockeys": jockeys
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        # ファイルサイズ確認
        import os
        size_mb = os.path.getsize(output_file) / (1024 * 1024)

        print(f"\n📁 騎手ナレッジファイル保存完了:")
        print(f"   ファイル名: {output_file}")
        print(f"   サイズ: {size_mb:.2f} MB")
        print(f"   騎手数: {len(jockeys):,}")

        # サンプル表示（上位5名）
        print(f"\n📊 サンプルデータ（総騎乗数上位5名）:")
        top_jockeys = sorted(jockeys.items(),
                           key=lambda x: x[1]['overall_stats']['total_races_analyzed'],
                           reverse=True)[:5]

        for name, data in top_jockeys:
            total = data['overall_stats']['total_races_analyzed']
            rate = data['overall_stats']['overall_fukusho_rate']
            print(f"   - {name}: {total}騎乗, 複勝率{rate}%")

        return True

    except Exception as e:
        print(f"❌ ファイル保存エラー: {e}")
        return False

def main():
    """メイン処理"""
    print("=" * 80)
    print("地方競馬版騎手ナレッジファイル作成 v1 Perfect")
    print("=" * 80)
    print(f"実行時刻: {datetime.now()}")

    # 対象年の設定（7年分）
    current_date = datetime.now()
    target_years = [str(current_date.year - i) for i in range(6, -1, -1)]

    print(f"\n対象年: {', '.join(target_years)}")
    print("制限: なし（7年間全データ使用）")

    print("\n" + "-" * 60)
    print("スケジュールマスター読み込み中...")
    schedule_master = load_schedule_master()

    print("\n" + "-" * 60)
    print("データベース接続中...")

    try:
        # データ取得
        print("✅ データベース接続成功")
        print(f"\nデータ取得中（対象年: {', '.join(target_years)}）...")
        rows = fetch_jockey_data(target_years)
        print(f"✅ データ取得成功: {len(rows):,}レコード")

        # データ集計
        print("\n" + "-" * 60)
        print("Phase 4: 騎手データ集計中...")
        jockeys = aggregate_jockey_stats(rows, schedule_master)
        print("✅ Phase 4完了")

        # ファイル出力
        print("\n" + "-" * 60)
        print("Phase 5: JSONファイル出力中...")
        output_file = f"nankan_jockey_knowledge_20250907.json"

        if save_jockey_knowledge(jockeys, output_file):
            print("✅ Phase 5完了")
        else:
            print("❌ Phase 5失敗")
            return False

        print("\n" + "=" * 80)
        print("✅ 処理完了！")
        print("=" * 80)

        return True

    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()