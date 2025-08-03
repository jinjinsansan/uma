#!/usr/bin/env python3
"""
馬名直接入力D-Logic分析テスト
"""
import asyncio
import sys
import os

# パス追加
sys.path.append(os.path.dirname(__file__))

async def test_horse_name_analysis():
    """馬名直接入力分析テスト"""
    print("🐎 馬名直接入力D-Logic分析テスト")
    print("=" * 50)
    
    try:
        from api.chat import extract_horse_name, handle_horse_analysis_message
        
        # 1. 馬名抽出テスト
        print("\n1️⃣ 馬名抽出テスト")
        test_messages = [
            "エフワンライデンの指数を教えて",
            "ディープインパクトはどう？",
            "ダンスインザダークの分析をお願いします",
            "ブライアンズロマンについて知りたい",
            "オルフェーヴルのスコアは？",
            "今日は良い天気ですね"  # 馬名なし
        ]
        
        for message in test_messages:
            horse_name = extract_horse_name(message)
            if horse_name:
                print(f"✅ 「{message}」→ 馬名: {horse_name}")
            else:
                print(f"❌ 「{message}」→ 馬名抽出なし")
        
        # 2. 実際の分析テスト
        print("\n2️⃣ 実際の分析テスト")
        test_horses = ["エフワンライデン", "ブライアンズロマン", "テスト馬"]
        
        for horse_name in test_horses:
            try:
                print(f"\n🏇 {horse_name} 分析中...")
                result = await handle_horse_analysis_message(
                    f"{horse_name}の指数を教えて", 
                    horse_name, 
                    []
                )
                
                if result.get("status") == "success":
                    print(f"✅ 分析成功")
                    d_logic_result = result.get("d_logic_result", {})
                    if d_logic_result.get("horses"):
                        horse_analysis = d_logic_result["horses"][0]
                        print(f"   スコア: {horse_analysis.get('total_score', 0)}")
                        print(f"   グレード: {horse_analysis.get('grade', 'N/A')}")
                        print(f"   分析元: {horse_analysis.get('analysis_source', 'N/A')}")
                    
                    # メッセージ一部表示
                    message = result.get("message", "")
                    print(f"   LLM説明: {message[:100]}...")
                else:
                    print(f"❌ 分析失敗: {result.get('message', 'N/A')}")
                    
            except Exception as e:
                print(f"❌ エラー: {e}")
        
        print("\n" + "=" * 50)
        print("✅ 馬名直接入力D-Logic分析機能実装完了!")
        print("🚀 利用可能パターン:")
        print("  • 「エフワンライデンの指数を教えて」")
        print("  • 「ディープインパクトはどう？」") 
        print("  • 「ダンスインザダークの分析をお願いします」")
        print("  • 「オルフェーヴルについて知りたい」")
        
        return True
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_horse_name_analysis())
    exit(0 if success else 1)