#!/usr/bin/env python3
"""
レーン騎手の確認
"""
from services.jockey_data_manager import jockey_manager

# 騎手ナレッジのキーを取得
all_keys = list(jockey_manager.jockey_knowledge.keys())

# レーン関連を探す
print("=== レーン関連の騎手名 ===")
for key in all_keys:
    if 'レーン' in key or 'レン' in key or 'Lane' in key.upper():
        print(f"'{key}' (長さ: {len(key)})")