"""
正規表現パターンのテスト
"""

import re

message = "オルフェーヴルの分析をして"

# カタカナまたは英字の連続を抽出
potential_horses = re.findall(r'[ア-ンー]+|[A-Za-z]+', message)
print(f"抽出された馬名候補: {potential_horses}")

for potential_horse in potential_horses:
    print(f"  候補: '{potential_horse}' (長さ: {len(potential_horse)})")
    
    # 助詞パターンのチェック
    if re.search(f'{potential_horse}(の|は|が|を|と|って|という)', message):
        print(f"    → 馬名パターンにマッチ！")
    else:
        print(f"    → 馬名パターンにマッチしない")

# 正しい範囲を確認
print("\nカタカナの範囲テスト:")
test_chars = ['オ', 'ル', 'フ', 'ェ', 'ー', 'ヴ', 'ァ', 'ィ', 'ゥ', 'ェ', 'ォ']
for char in test_chars:
    in_range = 'ア' <= char <= 'ン' or char == 'ー'
    print(f"  '{char}': {in_range}")