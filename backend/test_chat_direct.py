#!/usr/bin/env python3
"""
チャットAPI直接テスト
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from main import app
from fastapi.testclient import TestClient
import json

def test_chat_api():
    client = TestClient(app)
    
    print("=" * 50)
    print("チャットAPI直接テスト")
    print("=" * 50)
    
    # テストケース1: 本日の東京3Rの指数を出して
    print("\n1. メインテスト: 本日の東京3Rの指数を出して")
    print("-" * 30)
    
    chat_request = {
        "message": "本日の東京3Rの指数を出して",
        "request_type": "d_logic"
    }
    
    try:
        response = client.post("/api/chat", json=chat_request)
        print(f"ステータス: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"レスポンスタイプ: {data.get('type', 'N/A')}")
            print(f"メッセージ: {data.get('message', 'N/A')[:100]}...")
            
            # Dロジック結果確認
            response_data = data.get('data', {})
            if response_data:
                prediction = response_data.get('prediction', {})
                race_info = response_data.get('race_info', {})
                
                if prediction:
                    horses = prediction.get('horses', [])
                    print(f"Dロジック計算: {len(horses)}頭分析完了")
                    
                    if horses:
                        print("上位3頭の結果:")
                        for i, horse in enumerate(horses[:3], 1):
                            name = horse.get('horse_name', 'N/A')
                            score = horse.get('total_score', 0)
                            confidence = horse.get('confidence', 'N/A')
                            print(f"  {i}. {name}: {score:.1f}pts ({confidence})")
                
                if race_info:
                    print(f"レース情報: {race_info.get('raceName', 'N/A')}")
            
            print("\n✅ メインテスト成功!")
        else:
            print(f"❌ エラー: {response.status_code}")
            print(f"詳細: {response.text}")
            
    except Exception as e:
        print(f"❌ 例外エラー: {e}")
    
    # テストケース2: 他のパターン
    print("\n2. 追加テスト: 他のパターン")
    print("-" * 30)
    
    test_patterns = [
        "東京3Rの指数教えて",
        "3Rの指数を出して",
        "Dロジック計算して"
    ]
    
    for pattern in test_patterns:
        try:
            chat_request = {"message": pattern, "request_type": "d_logic"}
            response = client.post("/api/chat", json=chat_request)
            
            if response.status_code == 200:
                data = response.json()
                print(f"'{pattern}': SUCCESS - {data.get('type', 'N/A')}")
            else:
                print(f"'{pattern}': FAILED - {response.status_code}")
                
        except Exception as e:
            print(f"'{pattern}': ERROR - {e}")
    
    print("\n" + "=" * 50)
    print("チャットAPI直接テスト完了")
    print("=" * 50)

if __name__ == "__main__":
    test_chat_api()