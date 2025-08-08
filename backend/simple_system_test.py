#!/usr/bin/env python3
"""
🚀 D-Logic AI シンプルシステムテスト
基本機能の動作確認（requests使用）
"""
import requests
import json
import time

def test_basic_functionality():
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
        }
    ]
    
    print("🚀 D-Logic AI シンプルシステムテスト")
    print("=" * 60)
    
    success_count = 0
    total_count = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print(f"   入力: '{test_case['message']}'")
        
        start_time = time.time()
        
        try:
            response = requests.post(
                api_url,
                json={"message": test_case["message"], "history": []},
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
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
                
                if speed_ok and d_logic_ok:
                    status = "✅"
                    success_count += 1
                else:
                    status = "❌"
                
                print(f"   結果: {status}")
                print(f"   応答時間: {response_time:.2f}秒")
                print(f"   D-Logic: {has_d_logic} (期待: {test_case['expected_d_logic']})")
                if horse_name:
                    print(f"   検出馬名: {horse_name}")
                print(f"   レスポンス: {message[:100]}...")
                
            else:
                print(f"   ❌ HTTP エラー: {response.status_code}")
                
        except requests.exceptions.Timeout:
            print(f"   ⏰ タイムアウト (15秒超)")
        except Exception as e:
            print(f"   💥 エラー: {e}")
    
    print("\n" + "=" * 60)
    print(f"🎯 基本機能テスト完了: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
    
    if success_count == total_count:
        print("🎉 全テスト成功！システムは正常に動作しています")
    elif success_count >= total_count * 0.8:
        print("👍 概ね良好！一部に問題がありますが実用的です")
    else:
        print("⚠️ 問題あり：システムに重大な問題があります")

# メイン実行
if __name__ == "__main__":
    test_basic_functionality()