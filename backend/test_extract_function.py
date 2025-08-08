#!/usr/bin/env python3
"""
extract_horse_name関数の直接テスト
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from api.chat import extract_horse_name

# テストケース
test_cases = [
    "こんにちは",
    "おはようございます", 
    "こんばんは",
    "ありがとう",
    "何ですか",
    "教えて",
    "エフワンライデンの指数を教えて",
    "ディープインパクトはどう？",
    "レガレイラの分析をお願いします",
    "アーモンドアイについて",
    "コントレイル",
    "エフワンライデン",
    "今日の天気はどうですか",
    "競馬って面白いですね",
    "D-Logicとは何ですか"
]

print("🧪 extract_horse_name 関数テスト")
print("=" * 50)

for test in test_cases:
    result = extract_horse_name(test)
    status = "❌ 馬名検出" if result else "✅ スキップ"
    print(f"{status}: '{test}' → {result}")

print("=" * 50)
print("✅ = 正常（D-Logic分析スキップ）")
print("❌ = 異常（D-Logic分析実行）")