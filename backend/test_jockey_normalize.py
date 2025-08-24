#!/usr/bin/env python3
"""
騎手名正規化の動作確認
"""
from services.jockey_data_manager import jockey_manager
from services.jockey_name_mapper import normalize_jockey_name

# 騎手ナレッジの騎手名を確認
all_jockeys = list(jockey_manager.jockey_knowledge.keys())

# 外国人騎手を探す
foreign_jockeys = [j for j in all_jockeys if any(c in j for c in ['．', '.', 'J', 'C', 'M', 'D', 'W'])]
print(f"外国人騎手（推定）: {foreign_jockeys[:20]}")

# 横山系を探す
yokoyama_jockeys = [j for j in all_jockeys if j.startswith('横山')]
print(f"\n横山系騎手: {yokoyama_jockeys}")

# 吉田系を探す
yoshida_jockeys = [j for j in all_jockeys if j.startswith('吉田')]
print(f"\n吉田系騎手: {yoshida_jockeys}")

# netkeiba形式の騎手名をテスト
test_cases = [
    'ルメール',
    'C.ルメール',
    '横山武',
    '横山和',
    '吉田隼',
    '川田',
    '武豊'
]

print("\n\nnetkeiba形式 → 正規化 → ナレッジ確認:")
for name in test_cases:
    normalized = normalize_jockey_name(name)
    exists = normalized in all_jockeys
    print(f"{name:10} → {normalized:15} → {'✓' if exists else '✗'}")