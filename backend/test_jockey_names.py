#!/usr/bin/env python3
"""
騎手ナレッジの騎手名を確認
"""
from services.jockey_data_manager import jockey_manager

# 騎手ナレッジの騎手名を確認
all_jockeys = list(jockey_manager.jockey_knowledge.keys())
print(f"騎手総数: {len(all_jockeys)}")

# ルメール関連の騎手名を検索
lemaire_jockeys = [j for j in all_jockeys if 'ルメール' in j]
print(f"\n'ルメール'を含む騎手名: {lemaire_jockeys}")

# Cで始まる騎手名を検索
c_jockeys = [j for j in all_jockeys if j.startswith('C')]
print(f"\n'C'で始まる騎手名: {c_jockeys[:10]}")  # 最初の10名

# 騎手名正規化のテスト
from services.jockey_name_mapper import normalize_jockey_name

test_names = ['C.ルメール', 'ルメール', 'Cルメール', 'C．ルメール']
print("\n騎手名正規化テスト:")
for name in test_names:
    normalized = normalize_jockey_name(name)
    print(f"  '{name}' → '{normalized}' → ナレッジに存在: {normalized in all_jockeys}")