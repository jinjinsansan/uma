#!/usr/bin/env python3
"""
拡張ナレッジのデータ構造を確認
"""
from services.extended_knowledge_manager import get_extended_knowledge_manager

# 拡張ナレッジマネージャーを取得
manager = get_extended_knowledge_manager()

# イクイノックスのデータを確認
horse_data = manager.get_horse_data("イクイノックス")
if horse_data:
    print("イクイノックスのデータ構造:")
    print(f"データ型: {type(horse_data)}")
    if isinstance(horse_data, dict):
        print(f"キー: {list(horse_data.keys())[:10]}")  # 最初の10個のキー
        # racesがキーにあるか確認
        if 'races' in horse_data:
            print(f"races型: {type(horse_data['races'])}")
            if isinstance(horse_data['races'], list) and len(horse_data['races']) > 0:
                print(f"最初のレース: {horse_data['races'][0]}")
    elif isinstance(horse_data, list):
        print(f"リストの長さ: {len(horse_data)}")
        if len(horse_data) > 0:
            print(f"最初の要素: {horse_data[0]}")
else:
    print("イクイノックスのデータが見つかりません")

# 全体のデータ構造も確認
all_horses = manager.get_all_horses()
print(f"\n全馬データ数: {len(all_horses)}")
sample_horses = list(all_horses.keys())[:5]
print(f"サンプル馬名: {sample_horses}")

# サンプル馬のデータ構造を確認
if sample_horses:
    sample_data = all_horses[sample_horses[0]]
    print(f"\n{sample_horses[0]}のデータ型: {type(sample_data)}")
    if isinstance(sample_data, list) and len(sample_data) > 0:
        print(f"リストの長さ: {len(sample_data)}")
        print(f"最初の要素のキー: {list(sample_data[0].keys()) if isinstance(sample_data[0], dict) else 'Not a dict'}")