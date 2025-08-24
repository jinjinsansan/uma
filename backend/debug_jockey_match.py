#!/usr/bin/env python3
"""
騎手名マッチングのデバッグ
"""
from services.jockey_data_manager import jockey_manager

# 騎手ナレッジのキーを取得
all_keys = list(jockey_manager.jockey_knowledge.keys())

# ルメール関連を探す
print("=== ルメール関連の騎手名 ===")
for key in all_keys:
    if 'ルメール' in key or 'ルメ' in key or 'メール' in key:
        print(f"'{key}' (長さ: {len(key)}, bytes: {key.encode('utf-8')})")

# 武豊関連を探す
print("\n=== 武豊関連の騎手名 ===")
for key in all_keys:
    if '武豊' in key:
        print(f"'{key}' (長さ: {len(key)}, bytes: {key.encode('utf-8')})")

# get_jockey_dataメソッドのテスト
print("\n=== get_jockey_dataメソッドのテスト ===")
test_names = ['ルメール', 'C.ルメール', '武豊', '川田将雅']
for name in test_names:
    data = jockey_manager.get_jockey_data(name)
    if data:
        print(f"'{name}' → 見つかった")
    else:
        print(f"'{name}' → 見つからない")
        # 部分一致で探してみる
        for key in all_keys:
            if name in key.strip():
                print(f"  → 部分一致: '{key}'")