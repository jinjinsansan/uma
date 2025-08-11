#!/usr/bin/env python3
"""複数馬分析機能のテスト"""

from api.chat import extract_multiple_horse_names, extract_horse_name
from services.fast_dlogic_engine import FastDLogicEngine

# テストケース
test_cases = [
    # 単頭
    "ヤマニンバロネスの指数は？",
    "ドウデュース",
    
    # 2頭比較
    "ドウデュース、イクイノックス",
    "ヤマニンバロネスとサツキノジョウを比較",
    
    # 複数頭（カンマ区切り）
    "ドウデュース、イクイノックス、タイトルホルダー、ソダシ",
    
    # G1レース形式
    "2024年有馬記念 ドウデュース イクイノックス タイトルホルダー ソダシ スターズオンアース",
    
    # 本日レース形式
    "2025年8月新潟5R ヤマニンバロネス サツキノジョウ レガレイラ ダノンデサイル アーバンシック",
]

print("=" * 60)
print("複数馬名抽出テスト")
print("=" * 60)

for test in test_cases:
    print(f"\n入力: '{test}'")
    
    # 複数馬抽出
    horse_names, race_info = extract_multiple_horse_names(test)
    print(f"  複数馬抽出: {horse_names}")
    print(f"  レース情報: '{race_info}'")
    
    # 単頭抽出（比較用）
    single = extract_horse_name(test)
    print(f"  単頭抽出: '{single}'")

# FastDLogicEngineのテスト
print("\n" + "=" * 60)
print("FastDLogicEngine テスト")
print("=" * 60)

engine = FastDLogicEngine()

# 2頭比較
print("\n【2頭比較】")
horses = ["ヤマニンバロネス", "サツキノジョウ"]
result = engine.analyze_race_horses(horses)
for horse in result['horses']:
    total_score = horse.get('total_score', 0)
    if total_score is not None:
        print(f"{horse.get('horse_name', 'Unknown')}: {total_score:.2f}点 (rank: {horse.get('dlogic_rank', '-')})")
    else:
        print(f"{horse.get('horse_name', 'Unknown')}: データなし (rank: {horse.get('dlogic_rank', '-')})")

# 5頭分析
print("\n【5頭分析】")
horses = ["ヤマニンバロネス", "サツキノジョウ", "レガレイラ", "ダノンデサイル", "アーバンシック"]
result = engine.analyze_race_horses(horses)
print(f"分析完了: {result['race_analysis']['analyzed_horses']}頭")
print(f"計算時間: {result['race_analysis']['total_calculation_time']:.3f}秒")
print(f"平均時間: {result['race_analysis']['avg_time_per_horse']:.3f}秒/頭")
print("\nランキング:")
for horse in result['horses'][:5]:  # TOP5まで表示
    total_score = horse.get('total_score', 0)
    if total_score is not None:
        print(f"{horse.get('dlogic_rank', '-')}位: {horse.get('horse_name', 'Unknown')} - {total_score:.2f}点")
    else:
        print(f"{horse.get('dlogic_rank', '-')}位: {horse.get('horse_name', 'Unknown')} - データなし")