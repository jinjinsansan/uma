#!/usr/bin/env python3
"""
安全なクリーンテスト - 完全独立実行
"""
import sys
import os

# 完全クリーン環境
if __name__ == "__main__":
    # パス追加
    sys.path.insert(0, os.path.dirname(__file__))
    
    # モジュール強制リロード
    if 'api' in sys.modules:
        del sys.modules['api']
    if 'api.chat' in sys.modules:
        del sys.modules['api.chat']
    
    # 新規インポート
    from api.chat import extract_horse_name
    
    # 最重要テストケース
    critical_tests = [
        ("こんにちは", True),           # 高速スキップ必須
        ("おはようございます", True),    # 高速スキップ必須  
        ("エフワンライデンの指数を教えて", False), # D-Logic実行
        ("ディープインパクトはどう？", False),    # D-Logic実行
    ]
    
    print("🔒 安全なクリーンテスト実行")
    print("=" * 50)
    
    success_count = 0
    total_count = len(critical_tests)
    
    for test_input, should_skip in critical_tests:
        result = extract_horse_name(test_input)
        actual_skip = result is None
        
        if should_skip == actual_skip:
            status = "✅"
            success_count += 1
        else:
            status = "❌"
        
        action = "高速スキップ" if actual_skip else f"D-Logic実行({result})"
        print(f"{status} '{test_input}' → {action}")
    
    success_rate = (success_count / total_count) * 100
    print("=" * 50)
    print(f"🎯 成功率: {success_count}/{total_count} ({success_rate:.1f}%)")
    
    if success_rate == 100:
        print("🎉 完璧！修正が正常に反映されました！")
    else:
        print("⚠️ まだ問題があります")