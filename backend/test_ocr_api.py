#!/usr/bin/env python3
"""OCR APIのテスト"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_ocr_endpoint():
    """OCRエンドポイントのテスト"""
    print("=== OCR Endpoint Test ===")
    
    # テストエンドポイント
    response = requests.get(f"{BASE_URL}/api/admin/ocr-race/test")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
def test_today_races_storage():
    """レース情報保存APIのテスト"""
    print("\n=== Today Races Storage Test ===")
    
    # テストデータ
    test_race = {
        "race_date": "2025-08-09",
        "venue": "新潟",
        "race_number": 5,
        "race_name": "新潟日報賞",
        "horses": [
            "ヤマニンバロネス",
            "サツキノジョウ",
            "レガレイラ",
            "ダノンデサイル",
            "アーバンシック"
        ]
    }
    
    # レース情報を保存
    print("\n1. Saving race data...")
    response = requests.post(
        f"{BASE_URL}/api/today-races/ocr/",
        json=test_race
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    if response.status_code == 200:
        race_id = response.json().get("race_id")
        
        # レース一覧を取得
        print("\n2. Getting today's races...")
        response = requests.get(f"{BASE_URL}/api/today-races/ocr/")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        # 特定のレース詳細を取得
        print(f"\n3. Getting race detail for {race_id}...")
        response = requests.get(f"{BASE_URL}/api/today-races/ocr/{race_id}")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        # ストレージ状態を確認
        print("\n4. Checking storage status...")
        response = requests.get(f"{BASE_URL}/api/today-races/ocr/status/info")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

if __name__ == "__main__":
    print("OCR API Test Script")
    print("=" * 50)
    
    try:
        test_ocr_endpoint()
        test_today_races_storage()
    except requests.exceptions.ConnectionError:
        print("\nError: Cannot connect to backend server.")
        print("Make sure the server is running: python -m uvicorn main:app --reload")
    except Exception as e:
        print(f"\nUnexpected error: {e}")