#!/usr/bin/env python3
"""
🚀 D-Logic AI クイックシステムテスト
基本機能の動作確認
"""
import asyncio
import aiohttp
import json
import time

async def test_basic_functionality():
    """基本機能テスト"""
    api_url = "http://localhost:8000/api/chat/message"
    
    test_cases = [
        # 高速応答テスト（馬名なし）
        {
            "name": "挨拶テスト",
            "message": "こんにちは",
            "expected_fast": True,
            "expected_d_logic": False
        },
        {
            "name": "質問テスト",
            "message": "教えて",
            "expected_fast": True,
            "expected_d_logic": False
        },
        {
            "name": "システム質問",
            "message": "D-Logicとは",
            "expected_fast": True,
            "expected_d_logic": False
        },
        
        # 馬名検出テスト
        {
            "name": "馬名+インジケーター",
            "message": "ディープインパクトの指数を教えて",
            "expected_fast": False,
            "expected_d_logic": True
        },
        {
            "name": "馬名質問",
            "message": "エフワンライデンはどう？",
            "expected_fast": False,
            "expected_d_logic": True
        },
        {
            "name": "長い馬名単独",
            "message": "アーモンドアイ",
            "expected_fast": True,  # 8文字未満なので高速スキップ
            "expected_d_logic": False
        }
    ]
    
    print("🚀 D-Logic AI クイックシステムテスト")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{i}. {test_case['name']}")
            print(f"   入力: '{test_case['message']}'")
            
            start_time = time.time()
            
            try:
                async with session.post(
                    api_url,
                    json={"message": test_case["message"], "history": []},
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        end_time = time.time()
                        response_time = end_time - start_time
                        
                        has_d_logic = result.get("has_d_logic", False)
                        horse_name = result.get("horse_name", "")
                        message = result.get("message", "")
                        
                        # 結果判定
                        speed_ok = True
                        if test_case["expected_fast"] and response_time > 5:
                            speed_ok = False
                        elif not test_case["expected_fast"] and response_time > 30:
                            speed_ok = False
                        
                        d_logic_ok = has_d_logic == test_case["expected_d_logic"]
                        
                        status = "✅" if speed_ok and d_logic_ok else "❌"
                        
                        print(f"   結果: {status}")
                        print(f"   応答時間: {response_time:.2f}秒")
                        print(f"   D-Logic: {has_d_logic} (期待: {test_case['expected_d_logic']})")
                        if horse_name:
                            print(f"   検出馬名: {horse_name}")
                        print(f"   レスポンス: {message[:100]}...")
                        
                    else:
                        print(f"   ❌ HTTP エラー: {response.status}")
                        
            except asyncio.TimeoutError:
                print(f"   ⏰ タイムアウト (15秒超)")
            except Exception as e:
                print(f"   💥 エラー: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 基本機能テスト完了")

# メイン実行
if __name__ == "__main__":
    asyncio.run(test_basic_functionality())