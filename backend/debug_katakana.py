#!/usr/bin/env python3
"""
🔍 カタカナパターンデバッグ - 「こんにちは」問題の根本原因調査
"""
import re

def debug_katakana_detection(text: str):
    """カタカナパターン検出のデバッグ"""
    print(f"🔍 デバッグ対象: '{text}'")
    
    # 文字単位での詳細分析
    print(f"文字数: {len(text)}")
    for i, char in enumerate(text):
        unicode_code = ord(char)
        print(f"  {i+1}. '{char}' → Unicode: {unicode_code} (0x{unicode_code:04X})")
        
        # 各文字種の判定
        is_hiragana = '\u3041' <= char <= '\u3096'
        is_katakana = '\u30A1' <= char <= '\u30F6'
        is_katakana_extended = '\u30A1' <= char <= '\u30FC'  # ー含む
        
        print(f"      ひらがな: {is_hiragana}")
        print(f"      カタカナ: {is_katakana}")
        print(f"      カタカナ(拡張): {is_katakana_extended}")
    
    print()
    
    # パターンマッチングテスト
    patterns = [
        (r'[ァ-ヴー]{3,}', "現在のパターン"),
        (r'[\u30A1-\u30F6ー]{3,}', "Unicode正確版"),
        (r'[ア-ヴー]{3,}', "ア-ヴー版"),
        (r'[ァ-ヶー]{3,}', "ァ-ヶー版"),
    ]
    
    for pattern, description in patterns:
        matches = re.findall(pattern, text)
        print(f"パターン '{pattern}' ({description}): {matches}")
    
    print("=" * 60)

# テストケース
test_cases = [
    "こんにちは",           # ひらがなのみ - マッチしてはいけない
    "ディープインパクト",     # カタカナのみ - マッチすべき
    "エフワンライデン",       # カタカナのみ - マッチすべき  
    "アーモンドアイ",         # カタカナのみ - マッチすべき
    "こんにちはディープ",     # 混合 - カタカナ部分をマッチ
]

print("🔍 カタカナパターン検出デバッグ")
print("=" * 60)

for test in test_cases:
    debug_katakana_detection(test)