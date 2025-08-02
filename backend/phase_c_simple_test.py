#!/usr/bin/env python3
"""
Phase C: 本日レース統合テスト（簡易版）
「本日の東京3Rの指数を出して」完全動作確認
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from main import app
from fastapi.testclient import TestClient

def phase_c_simple_test():
    """Phase C簡易テスト"""
    client = TestClient(app)
    
    print("=" * 50)
    print("PHASE C SIMPLE TEST")
    print("=" * 50)
    
    # 1. 本日レースAPI
    print("\n1. Today Races API")
    response = client.get("/api/today-races")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Racecourses: {len(data.get('racecourses', []))}")
        print(f"Date: {data.get('date', 'N/A')}")
    
    # 2. レース詳細API
    print("\n2. Race Detail API")
    response = client.get("/api/race-detail/tokyo_3r")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        race_info = data.get('raceInfo', {})
        print(f"Race: {race_info.get('raceName', 'N/A')}")
        print(f"Horses: {len(data.get('horses', []))}")
    
    # 3. チャット統合テスト
    print("\n3. Chat Integration Test")
    chat_request = {
        "message": "本日の東京3Rの指数を出して",
        "request_type": "d_logic"
    }
    response = client.post("/api/chat", json=chat_request)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Type: {data.get('type', 'N/A')}")
        print(f"Message: {data.get('message', 'N/A')[:50]}...")
        
        # Dロジック結果確認
        response_data = data.get('data', {})
        if response_data:
            prediction = response_data.get('prediction', {})
            if prediction:
                horses = prediction.get('horses', [])
                print(f"D-Logic horses: {len(horses)}")
                if horses:
                    print(f"Top horse: {horses[0].get('horse_name', 'N/A')} - {horses[0].get('total_score', 0):.1f}pts")
    
    print("\n" + "=" * 50)
    print("PHASE C TEST COMPLETE")
    print("=" * 50)

if __name__ == "__main__":
    phase_c_simple_test()