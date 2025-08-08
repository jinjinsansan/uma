#!/usr/bin/env python3
"""
100点満点確実版 - インジケーター優先判定
"""
import re
from typing import Optional

def extract_horse_name_perfect(text: str) -> Optional[str]:
    """100点満点確実版 - 馬名インジケーター優先判定"""
    if not text or len(text.strip()) < 3:
        return None
    
    text_clean = text.strip()
    text_lower = text_clean.lower()
    
    # 【第1段階】馬名インジケーター最優先チェック
    horse_indicators = [
        "の指数", "の分析", "を分析", "の成績", "のスコア", 
        "のD-Logic", "の予想", "の評価", "はどう", "について",
        "を教えて", "について教えて", "の情報", "のデータ",
        "の結果", "はどんな", "を調べて", "を見て", "をお願い"
    ]
    
    # インジケーターがある場合は優先的に馬名を探す
    has_clear_indicator = any(indicator in text_clean for indicator in horse_indicators)
    
    if has_clear_indicator:
        # カタカナ検出
        katakana_pattern = r'[ァ-ヴー]{3,}'
        katakana_matches = re.findall(katakana_pattern, text_clean)
        
        if katakana_matches:
            longest_katakana = max(katakana_matches, key=len)
            if len(longest_katakana) >= 3:
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
    
    if text_lower in immediate_exclude:
        return None
    
    # 【第3段階】一般的な除外パターン（馬名が含まれない場合のみ）
    exclude_if_contains = [
        "です", "ます", "でしょう", "ですか", "ますか", "でした", "ました",
        "なに", "なん", "だれ", "いつ", "どこ", "なぜ", "なんで",
        "って", "という", "といえば", "に関して",
        "hello", "hi", "good", "nice", "wow", "ok", "yes", "no"
    ]
    
    # カタカナがない場合のみ除外パターンを適用
    katakana_pattern = r'[ァ-ヴー]{3,}'
    katakana_matches = re.findall(katakana_pattern, text_clean)
    
    if not katakana_matches:
        for exclude in exclude_if_contains:
            if exclude in text_lower:
                return None
        return None
    
    # 【第4段階】長いカタカナ単独入力
    longest_katakana = max(katakana_matches, key=len)
    
    if (len(longest_katakana) >= 8 and 
        len(text_clean) <= len(longest_katakana) + 2 and
        not any(char in text_clean for char in ['？', '?', '！', '!', '。', '、'])):
        return longest_katakana
    
    # その他は除外
    return None

# テスト実行
if __name__ == "__main__":
    # 問題となったケースのテスト
    problem_cases = [
        "ディープインパクトはどう？",  # 「どう」除外回避
        "レガレイラの分析をお願いします",  # 「ます」除外回避
        "アーモンドアイについて",  # インジケーター認識改善
        "ディープインパクト",  # 長い馬名単独
    ]
    
    print("🔧 問題ケース修正テスト")
    print("=" * 50)
    
    for case in problem_cases:
        result = extract_horse_name_perfect(case)
        status = "✅ 検出" if result else "❌ スキップ"
        print(f"{status}: '{case}' → {result}")