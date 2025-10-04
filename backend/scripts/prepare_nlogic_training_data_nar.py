"""
N-Logic (地方競馬版) 学習データ準備スクリプト
地方競馬ナレッジからレース結果を抽出し、特徴量付きCSVを生成
"""

import os
import sys
import pandas as pd

# バックエンドパスを追加
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from services.local_dlogic_raw_data_manager_v2 import local_dlogic_manager_v2


def extract_race_results_from_local_knowledge(local_manager):
    """地方競馬ナレッジからレース結果を抽出"""
    print("=" * 60)
    print("Step 1: 地方競馬ナレッジからレース結果抽出")
    print("=" * 60)

    race_records = []
    horse_names = local_manager.get_all_horse_names()
    total_horses = len(horse_names)

    print(f"処理中: {total_horses}頭の馬データ...")

    for idx, horse_name in enumerate(horse_names, start=1):
        if idx % 1000 == 0:
            print(f"  進捗: {idx}/{total_horses} ({idx/total_horses*100:.1f}%)")

        horse_data = local_manager.get_horse_raw_data(horse_name)
        if not horse_data:
            continue

        races = horse_data.get('races', [])
        for race in races:
            actual_rank = _safe_int(race.get('KAKUTEI_CHAKUJUN'))
            if actual_rank <= 0 or actual_rank >= 99:
                continue

            odds_value = _safe_int(race.get('TANSHO_ODDS'))
            if odds_value <= 0:
                continue
            actual_odds = odds_value / 10.0

            venue_code = str(race.get('KEIBAJO_CODE', '00')).zfill(2)
            race_number = _safe_int(race.get('RACE_BANGO'))
            distance = _safe_int(race.get('KYORI'))

            kaisai_nen = str(race.get('KAISAI_NEN', '')).strip()
            kaisai_gappi = str(race.get('KAISAI_GAPPI', '')).strip()
            if not kaisai_nen or not kaisai_gappi:
                continue

            date_str = kaisai_nen + kaisai_gappi.zfill(4)
            if len(date_str) != 8:
                continue

            race_id = f"{date_str}-{venue_code}-{race_number}"

            venue_name = race.get('track_name') or _NAR_VENUE_CODE_MAP.get(venue_code, '不明')

            race_records.append({
                'race_id': race_id,
                'date': date_str,
                'venue_code': venue_code,
                'venue_name': venue_name,
                'race_number': race_number,
                'distance': distance,
                'horse_name': horse_name,
                'actual_rank': actual_rank,
                'actual_odds': actual_odds,
            })

    df = pd.DataFrame(race_records)

    print(f"✅ {len(df)}件のレース結果を抽出")
    print(f"   ユニークレース数: {df['race_id'].nunique()}")
    print(f"   ユニーク馬数: {df['horse_name'].nunique()}")

    return df


def add_features(df, local_manager):
    """特徴量を追加"""
    print("\n" + "=" * 60)
    print("Step 2: 特徴量計算")
    print("=" * 60)

    race_counts = df['race_id'].value_counts().to_dict()
    features_list = []
    total = len(df)

    print(f"特徴量計算開始（{total}件）...")

    for idx, row in df.iterrows():
        if (idx + 1) % 1000 == 0:
            print(f"  処理中: {idx + 1}/{total} ({(idx+1)/total*100:.1f}%)")

        horse_name = row['horse_name']
        venue_code = str(row['venue_code']).zfill(2)
        venue = row.get('venue_name', _NAR_VENUE_CODE_MAP.get(venue_code, '不明'))
        distance = int(row['distance']) if pd.notna(row['distance']) else 1600

        horse_data = local_manager.get_horse_data(horse_name)

        if horse_data and 'races' in horse_data:
            races = horse_data['races']

            total_races = len(races)
            wins = sum(1 for r in races if _safe_int(r.get('KAKUTEI_CHAKUJUN')) == 1)
            places = sum(1 for r in races if _safe_int(r.get('KAKUTEI_CHAKUJUN')) <= 3)

            win_rate = wins / total_races if total_races > 0 else 0.0
            place_rate = places / total_races if total_races > 0 else 0.0

            finishes = [_safe_int(r.get('KAKUTEI_CHAKUJUN')) for r in races
                        if _safe_int(r.get('KAKUTEI_CHAKUJUN')) > 0]
            avg_finish = sum(finishes) / len(finishes) if finishes else 10.0

            popularities = [_safe_int(r.get('TANSHO_NINKIJUN', r.get('NINKIJUN')))
                            for r in races if _safe_int(r.get('TANSHO_NINKIJUN', r.get('NINKIJUN'))) > 0]
            avg_popularity = sum(popularities) / len(popularities) if popularities else 8.0

            corner4s = [_safe_int(r.get('CORNER4_JUNI')) for r in races
                        if _safe_int(r.get('CORNER4_JUNI')) > 0]
            avg_corner4 = sum(corner4s) / len(corner4s) if corner4s else 8.0

            kohan3fs = [_safe_int(r.get('KOHAN3F_TIME', r.get('KOHAN_3F')))
                        for r in races if _safe_int(r.get('KOHAN3F_TIME', r.get('KOHAN_3F'))) > 0]
            avg_kohan3f = sum(kohan3fs) / len(kohan3fs) if kohan3fs else 400

            track_races = [r for r in races if str(r.get('KEIBAJO_CODE', '')).zfill(2) == venue_code]

            if track_races:
                track_wins = sum(1 for r in track_races if _safe_int(r.get('KAKUTEI_CHAKUJUN')) == 1)
                track_win_rate = track_wins / len(track_races)

                track_finishes = [_safe_int(r.get('KAKUTEI_CHAKUJUN'))
                                   for r in track_races if _safe_int(r.get('KAKUTEI_CHAKUJUN')) > 0]
                track_avg_finish = sum(track_finishes) / len(track_finishes) if track_finishes else 10.0
            else:
                track_win_rate = 0.0
                track_avg_finish = 10.0

            similar_races = [r for r in races if abs(_safe_int(r.get('KYORI')) - distance) <= 200]
            if similar_races:
                distance_wins = sum(1 for r in similar_races if _safe_int(r.get('KAKUTEI_CHAKUJUN')) == 1)
                distance_aptitude = distance_wins / len(similar_races)
            else:
                distance_aptitude = 0.5

        else:
            total_races = 0
            win_rate = 0.0
            place_rate = 0.0
            avg_finish = 10.0
            avg_popularity = 8.0
            avg_corner4 = 8.0
            avg_kohan3f = 400
            track_win_rate = 0.0
            track_avg_finish = 10.0
            distance_aptitude = 0.5

        actual_odds = row['actual_odds']
        if pd.notna(actual_odds) and actual_odds > 0:
            actual_support_rate = 0.8 / actual_odds
        else:
            actual_support_rate = 0.0

        jockey_win_rate = 0.12
        jockey_place_rate = 0.32

        horse_count = int(race_counts.get(row['race_id'], 0))
        horse_count = horse_count if horse_count > 0 else 10

        features = {
            'race_id': row['race_id'],
            'horse_name': horse_name,
            'actual_rank': int(row['actual_rank']),
            'actual_odds': actual_odds if pd.notna(actual_odds) else 0.0,
            'actual_support_rate': actual_support_rate,
            'knowledge_total_races': total_races,
            'knowledge_win_rate': win_rate,
            'knowledge_place_rate': place_rate,
            'knowledge_avg_finish': avg_finish,
            'knowledge_avg_popularity': avg_popularity,
            'knowledge_avg_corner4': avg_corner4,
            'knowledge_avg_kohan3f': avg_kohan3f,
            'track_win_rate': track_win_rate,
            'track_avg_finish': track_avg_finish,
            'distance_aptitude': distance_aptitude,
            'jockey_win_rate': jockey_win_rate,
            'jockey_place_rate': jockey_place_rate,
            'venue_code': int(venue_code),
            'distance': distance,
            'horse_count': horse_count,
        }

        features_list.append(features)

    print("✅ 特徴量計算完了")

    return pd.DataFrame(features_list)


def _safe_int(value, default=0):
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return default


_NAR_VENUE_CODE_MAP = {
    '31': '門別', '32': '北見', '33': '岩見沢', '34': '帯広',
    '35': '旭川', '36': '札幌', '37': '函館', '38': '三条',
    '39': '新潟', '40': '足利', '41': '宇都宮', '42': '高崎',
    '43': '前橋', '44': '大井', '45': '川崎', '46': '船橋',
    '47': '浦和', '48': '水沢', '49': '盛岡', '50': '上山',
    '51': '三条2', '52': '新潟2', '53': '福山', '54': '益田',
    '55': '高知', '56': '佐賀', '57': '荒尾', '58': '中津',
    '59': '園田', '60': '姫路', '61': '名古屋', '62': '笠松',
    '63': '帯広ば', '64': '金沢', '65': '札幌ば', '66': '旭川ば'
}


def main():
    print("\n🚀 N-Logic (地方競馬) 学習データ準備")
    print("=" * 60)

    local_manager = local_dlogic_manager_v2
    print(f"✅ 地方ナレッジデータ読み込み完了: {len(local_manager.get_all_horse_names())}頭")

    df_results = extract_race_results_from_local_knowledge(local_manager)
    df_with_features = add_features(df_results, local_manager)

    print("\n" + "=" * 60)
    print("Step 3: データ保存")
    print("=" * 60)

    output_path = os.path.join(os.path.dirname(__file__), 'nlogic_training_data_nar.csv')
    df_with_features.to_csv(output_path, index=False)

    print(f"✅ 学習データ保存: {output_path}")
    print(f"   総レコード数: {len(df_with_features)}")
    print(f"   ユニークレース数: {df_with_features['race_id'].nunique()}")
    print(f"   ファイルサイズ: {os.path.getsize(output_path) / 1024 / 1024:.2f} MB")

    print("\n【データ統計】")
    print(f"  総レース数: {df_with_features['race_id'].nunique()}")
    print(f"  総馬数: {df_with_features['horse_name'].nunique()}")
    print(f"  平均出走頭数: {len(df_with_features) / df_with_features['race_id'].nunique():.1f}頭/レース")

    print("\n🎉 地方競馬版学習データ準備完了！")
    print("\n次のステップ:")
    print(f"  python3 scripts/train_nlogic_model.py --data {output_path} --model-prefix nlogic_nar")


if __name__ == '__main__':
    main()
