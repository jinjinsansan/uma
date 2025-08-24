#!/usr/bin/env python3
"""
ILogic（レースアナリシス）の騎手データ取得テスト
"""
from services.race_analysis_engine import get_race_analysis_engine
from services.fast_dlogic_engine import fast_engine_instance
from services.jockey_name_mapper import normalize_jockey_name
from services.jockey_data_manager import jockey_manager

# レース分析エンジンの取得
engine = get_race_analysis_engine(fast_engine_instance)
print("ILogic（レースアナリシス）エンジンを初期化")

# テストデータ
test_race = {
    'venue': '東京',
    'race_number': 11,
    'race_name': 'テスト記念（G2）',
    'grade': 'G2',
    'distance': '2400m',
    'track_condition': '良',
    'horses': ['イクイノックス', 'ドウデュース'],
    'jockeys': ['C.ルメール', '武豊'],
    'posts': [1, 2],
    'horse_numbers': [1, 2]
}

print("\n騎手名正規化テスト:")
for jockey in test_race['jockeys']:
    normalized = normalize_jockey_name(jockey)
    jockey_data = jockey_manager.get_jockey_data(normalized)
    print(f"  '{jockey}' → '{normalized}' → データ: {'あり' if jockey_data else 'なし'}")

# レース分析実行
print("\nレース分析実行:")
result = engine.analyze_race(test_race)

if 'results' in result:
    for horse_result in result['results']:
        print(f"\n{horse_result['horse']} × {horse_result['jockey']}:")
        print(f"  総合スコア: {horse_result['total_score']}点")
        print(f"  馬スコア: {horse_result['horse_score']}点")
        print(f"  騎手スコア: {horse_result['jockey_score']}点")