#!/usr/bin/env python3
"""
extract_horse_name関数のステップバイステップデバッグ
"""
import re

def extract_horse_name_debug(text: str):
    """デバッグ版extract_horse_name"""
    print(f"\n=== デバッグ: '{text}' ===")
    
    if not text or len(text.strip()) < 3:
        print("→ 終了: 短すぎる文字列")
        return None
    
    text_clean = text.strip()
    text_lower = text_clean.lower()
    print(f"→ クリーン済み: '{text_clean}' (小文字: '{text_lower}')")
    
    # 即座除外チェック
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
    
    print(f"→ 即座除外チェック...")
    if text_lower in immediate_exclude:
        print(f"→ ✅ 即座除外対象で発見: '{text_lower}'")
        return None
    else:
        print(f"→ 即座除外リストにはなし")
    
    # 部分一致チェック
    exclude_if_contains = [
        "です", "ます", "でしょう", "ですか", "ますか", "でした", "ました",
        "どう", "なに", "なん", "だれ", "いつ", "どこ", "なぜ", "なんで",
        "って", "という", "といえば", "について", "に関して",
        "hello", "hi", "good", "nice", "wow", "ok", "yes", "no"
    ]
    
    print(f"→ 部分一致除外チェック...")
    for exclude in exclude_if_contains:
        if exclude in text_lower:
            print(f"→ ✅ 部分一致で除外: '{exclude}' が含まれている")
            return None
    print(f"→ 部分一致除外なし")
    
    # カタカナチェック
    katakana_pattern = r'[ァ-ヴー]{3,}'
    katakana_matches = re.findall(katakana_pattern, text_clean)
    print(f"→ カタカナマッチ: {katakana_matches}")
    
    if not katakana_matches:
        print("→ ✅ カタカナなしで除外")
        return None
    
    longest_katakana = max(katakana_matches, key=len)
    print(f"→ 最長カタカナ: '{longest_katakana}' (長さ: {len(longest_katakana)})")
    
    # インジケーターチェック
    horse_indicators = [
        "の指数", "の分析", "を分析", "の成績", "のスコア", 
        "のD-Logic", "の予想", "の評価", "はどう", "について",
        "を教えて", "について教えて", "の情報", "のデータ",
        "の結果", "はどんな", "を調べて", "を見て"
    ]
    
    has_clear_indicator = any(indicator in text_clean for indicator in horse_indicators)
    print(f"→ インジケーター: {has_clear_indicator}")
    
    if has_clear_indicator and len(longest_katakana) >= 3:
        print(f"→ ❌ インジケーター付きで馬名検出: '{longest_katakana}'")
        return longest_katakana
    
    # 長いカタカナ単独チェック
    if (len(longest_katakana) >= 10 and 
        len(text_clean) <= len(longest_katakana) + 1 and
        not any(char in text_clean for char in ['？', '?', '！', '!', '。', '、', 'は', 'を', 'に', 'が', 'の', 'で', 'と'])):
        print(f"→ ❌ 長いカタカナ単独で馬名検出: '{longest_katakana}'")
        return longest_katakana
    
    print("→ ✅ 全条件をクリアして除外")
    return None

# テスト実行
test_cases = [
    "こんにちは",
    "おはようございます", 
    "エフワンライデンの指数を教えて",
]

print("🧪 ステップバイステップデバッグ")
print("=" * 60)

for test in test_cases:
    result = extract_horse_name_debug(test)
    print(f"最終結果: {result}")
    print("-" * 60)