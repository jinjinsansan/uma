#!/usr/bin/env python3
"""
🔍 extract_horse_name関数のステップバイステップデバッグ
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from api.chat import extract_horse_name
import re

def debug_extract_horse_name_step_by_step(text: str):
    """extract_horse_name関数のステップバイステップ実行"""
    print(f"🔍 デバッグ対象: '{text}'")
    print("=" * 60)
    
    if not text or len(text.strip()) < 3:
        print("❌ 文字数不足でreturn None")
        return None
    
    text_clean = text.strip()
    text_lower = text_clean.lower()
    print(f"✅ text_clean: '{text_clean}'")
    print(f"✅ text_lower: '{text_lower}'")
    
    # 【第1段階】馬名インジケーター最優先チェック
    horse_indicators = [
        "の指数", "の分析", "を分析", "の成績", "のスコア", 
        "のD-Logic", "の予想", "の評価", "はどう", "について",
        "を教えて", "について教えて", "の情報", "のデータ",
        "の結果", "はどんな", "を調べて", "を見て", "をお願い"
    ]
    
    has_clear_indicator = any(indicator in text_clean for indicator in horse_indicators)
    print(f"✅ 馬名インジケーター: {has_clear_indicator}")
    if has_clear_indicator:
        found_indicators = [indicator for indicator in horse_indicators if indicator in text_clean]
        print(f"   見つかったインジケーター: {found_indicators}")
    
    if has_clear_indicator:
        print("🔍 第1段階: インジケーターありでカタカナ検出")
        katakana_pattern = r'[ァ-ヴー]{3,}'
        katakana_matches = re.findall(katakana_pattern, text_clean)
        print(f"   カタカナマッチ: {katakana_matches}")
        
        if katakana_matches:
            longest_katakana = max(katakana_matches, key=len)
            if len(longest_katakana) >= 3:
                print(f"✅ 第1段階で馬名検出: '{longest_katakana}'")
                return longest_katakana
    
    # 【第2段階】明確な除外対象チェック
    immediate_exclude = [
        "こんにちは", "こんにちわ", "おはよう", "おはようございます", 
        "こんばんは", "こんばんわ", "お疲れ様", "お疲れさま", "お疲れ",
        "ありがとう", "ありがとうございます", "よろしく", "はじめまして",
        "さようなら", "またね", "お元気", "元気",
        "何ですか", "誰ですか", "どうですか", "なんですか", "だれですか",
        "教えて", "説明して", "わからない", "知りたい",
        "D-Logicとは", "使い方", "やり方", "方法", "テスト", "test",
        "あなたは", "君は", "きみは",
        "今日の天気", "天気", "時間", "日付", "曜日", "今日", "明日", "昨日",
        "暑い", "寒い", "雨", "晴れ", "面白い", "楽しい", "すごい"
    ]
    
    print("🔍 第2段階: 即座除外チェック")
    if text_lower in immediate_exclude:
        print(f"✅ 即座除外リストにマッチ: '{text_lower}'")
        return None
    else:
        print("❌ 即座除外リストにマッチしない")
    
    # 【第3段階】一般的な除外パターン（馬名が含まれない場合のみ）
    exclude_if_contains = [
        "です", "ます", "でしょう", "ですか", "ますか", "でした", "ました",
        "なに", "なん", "だれ", "いつ", "どこ", "なぜ", "なんで",
        "って", "という", "といえば", "に関して",
        "hello", "hi", "good", "nice", "wow", "ok", "yes", "no"
    ]
    
    print("🔍 第3段階: 一般除外パターンチェック")
    # カタカナがない場合のみ除外パターンを適用
    katakana_pattern = r'[ァ-ヴー]{3,}'
    katakana_matches = re.findall(katakana_pattern, text_clean)
    print(f"   カタカナマッチ（第3段階）: {katakana_matches}")
    
    if not katakana_matches:
        print("   カタカナなし → 除外パターン適用")
        for exclude in exclude_if_contains:
            if exclude in text_lower:
                print(f"✅ 除外パターンにマッチ: '{exclude}' in '{text_lower}'")
                return None
        print("✅ カタカナなしでreturn None")
        return None
    else:
        print("   カタカナあり → 除外パターン適用せず")
    
    # 【第4段階】長いカタカナ単独入力
    print("🔍 第4段階: 長いカタカナ単独入力チェック")
    longest_katakana = max(katakana_matches, key=len)
    print(f"   最長カタカナ: '{longest_katakana}' (長さ: {len(longest_katakana)})")
    
    condition1 = len(longest_katakana) >= 8
    condition2 = len(text_clean) <= len(longest_katakana) + 2
    condition3 = not any(char in text_clean for char in ['？', '?', '！', '!', '。', '、'])
    
    print(f"   条件1（8文字以上）: {condition1}")
    print(f"   条件2（テキスト長制限）: {condition2} ({len(text_clean)} <= {len(longest_katakana) + 2})")
    print(f"   条件3（記号なし）: {condition3}")
    
    if condition1 and condition2 and condition3:
        print(f"✅ 第4段階で馬名検出: '{longest_katakana}'")
        return longest_katakana
    
    print("❌ その他は除外でreturn None")
    return None

# 問題のケースをテスト
test_case = "こんにちは"
print("🔍 extract_horse_name関数 完全デバッグ")
print("=" * 80)

result = debug_extract_horse_name_step_by_step(test_case)
print("=" * 80)
print(f"🎯 最終結果: {result}")
print()

# 実際の関数でも確認
actual_result = extract_horse_name(test_case)
print(f"🔍 実際の関数結果: {actual_result}")
print(f"🔍 一致確認: {result == actual_result}")