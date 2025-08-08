#!/usr/bin/env python3
"""
モジュール強制リロードテスト
"""
import sys
import os
import importlib

sys.path.append(os.path.dirname(__file__))

# 既存モジュールを削除
if 'api.chat' in sys.modules:
    del sys.modules['api.chat']
if 'api' in sys.modules:
    del sys.modules['api']

# 新しくインポート
from api.chat import extract_horse_name

# テストケース
test_cases = [
    "こんにちは",
    "おはようございます", 
    "こんばんは",
    "ありがとう",
    "エフワンライデンの指数を教えて",
    "コントレイル",
    "今日の天気はどうですか"
]

print("🧪 モジュール強制リロード後テスト")
print("=" * 50)

for test in test_cases:
    result = extract_horse_name(test)
    status = "❌ 馬名検出" if result else "✅ スキップ"
    print(f"{status}: '{test}' → {result}")

print("=" * 50)