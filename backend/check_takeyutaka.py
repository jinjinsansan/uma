#!/usr/bin/env python3
"""
武豊の存在確認
"""
from services.jockey_data_manager import jockey_manager

# 騎手ナレッジの騎手名を確認
all_jockeys = list(jockey_manager.jockey_knowledge.keys())

# 武豊関連を探す
take_jockeys = [j for j in all_jockeys if '武' in j and '豊' in j]
print(f"武豊関連: {take_jockeys}")

# 武で始まる騎手
take_start = [j for j in all_jockeys if j.startswith('武')]
print(f"\n武で始まる: {take_start}")

# 豊を含む騎手
yutaka = [j for j in all_jockeys if '豊' in j]
print(f"\n豊を含む: {yutaka[:10]}")

# スペースが含まれる騎手（吉田豊の後ろにスペースがある）
space_jockeys = [j for j in all_jockeys if ' ' in j or '　' in j]
print(f"\nスペース含む騎手: {len(space_jockeys)}名")
print(f"例: {space_jockeys[:10]}")

# 正確な武豊を探す
if '武豊' in all_jockeys:
    print("\n武豊: 存在する")
elif '武豊　' in all_jockeys:
    print("\n武豊　（全角スペース付き）: 存在する")
elif '武豊 ' in all_jockeys:
    print("\n武豊 （半角スペース付き）: 存在する")
else:
    print("\n武豊: 見つからない")