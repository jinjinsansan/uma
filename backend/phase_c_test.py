#!/usr/bin/env python3
"""
Phase C: 本日レース統合テスト
「本日の東京3Rの指数を出して」完全動作確認
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from main import app
from fastapi.testclient import TestClient

def phase_c_integration_test():
    """Phase C: 本日レース統合・完璧ユーザー体験実装のテスト"""
    client = TestClient(app)
    
    print("=" * 60)
    print("PHASE C: 本日レース統合・完璧ユーザー体験実装テスト")
    print("=" * 60)
    
    test_results = {}
    
    # 1. 新しい本日レースAPI確認
    print("\n1. 本日レースAPI (Phase C)")
    print("-" * 30)
    try:
        response = client.get("/api/today-races")
        test_results['today_races_api'] = response.status_code == 200
        
        if response.status_code == 200:
            data = response.json()
            racecourses = data.get('racecourses', [])
            total_races = sum(len(course.get('races', [])) for course in racecourses)
            
            print(f"Status: SUCCESS (200)")
            print(f"Date: {data.get('date', 'N/A')}")
            print(f"Last Update: {data.get('lastUpdate', 'N/A')}")
            print(f"Total Racecourses: {len(racecourses)}")
            print(f"Total Races: {total_races}")
            
            for course in racecourses:
                print(f"  {course.get('name', 'N/A')}: {len(course.get('races', []))} races")
        else:
            print(f"Status: FAILED ({response.status_code})")
            print(f"Error: {response.text}")
            
    except Exception as e:
        test_results['today_races_api'] = False
        print(f"Error: {e}")
    
    # 2. レース詳細API確認
    print("\n2. レース詳細API (Phase C)")
    print("-" * 30)
    try:
        response = client.get("/api/race-detail/tokyo_3r")
        test_results['race_detail_api'] = response.status_code == 200
        
        if response.status_code == 200:
            data = response.json()
            race_info = data.get('raceInfo', {})
            horses = data.get('horses', [])
            
            print(f"Status: SUCCESS (200)")
            print(f"Race: {race_info.get('raceName', 'N/A')}")
            print(f"Time: {race_info.get('time', 'N/A')}")
            print(f"Distance: {race_info.get('distance', 'N/A')}")
            print(f"Track: {race_info.get('track', 'N/A')}")
            print(f"Horses: {len(horses)} entries")
            
            if horses:
                print(f"Sample horses:")
                for horse in horses[:3]:
                    print(f"  - {horse.get('name', 'N/A')} ({horse.get('jockey', 'N/A')})")
        else:
            print(f"Status: FAILED ({response.status_code})")
            print(f"Error: {response.text}")
            
    except Exception as e:
        test_results['race_detail_api'] = False
        print(f"Error: {e}")
    
    # 3. レース検索API確認
    print("\n3. レース検索API (Phase C)")
    print("-" * 30)
    try:
        response = client.get("/api/race-search?course_id=tokyo&race_number=3")
        test_results['race_search_api'] = response.status_code == 200
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('searchResults', [])
            
            print(f"Status: SUCCESS (200)")
            print(f"Search Results: {len(results)} races found")
            print(f"Result Count: {data.get('resultCount', 0)}")
            
            if results:
                race = results[0]
                print(f"Found Race:")
                print(f"  Race ID: {race.get('raceId', 'N/A')}")
                print(f"  Name: {race.get('raceName', 'N/A')}")
                print(f"  Course: {race.get('racecourse', {}).get('name', 'N/A')}")
        else:
            print(f"Status: FAILED ({response.status_code})")
            print(f"Error: {response.text}")
            
    except Exception as e:
        test_results['race_search_api'] = False
        print(f"Error: {e}")
    
    # 4. チャット統合テスト（メインテスト）
    print("\n4. チャット統合テスト: 「本日の東京3Rの指数を出して」")
    print("-" * 30)
    try:
        chat_request = {
            "message": "本日の東京3Rの指数を出して",
            "request_type": "d_logic"
        }
        response = client.post("/api/chat", json=chat_request)
        test_results['chat_integration'] = response.status_code == 200
        
        if response.status_code == 200:
            data = response.json()
            print(f"Status: SUCCESS (200)")
            print(f"Response Type: {data.get('type', 'N/A')}")
            print(f"Message: {data.get('message', 'N/A')[:100]}...")
            
            # Dロジック結果確認
            response_data = data.get('data', {})
            prediction = response_data.get('prediction', {})
            race_info = response_data.get('race_info', {})
            
            if prediction:
                horses = prediction.get('horses', [])
                print(f"D-Logic Calculation: SUCCESS")
                print(f"Horses Analyzed: {len(horses)}")
                print(f"Race Info: {race_info.get('raceName', 'N/A')}")
                
                if horses:
                    print(f"Top 3 D-Logic Results:")
                    for i, horse in enumerate(horses[:3], 1):
                        name = horse.get('horse_name', 'N/A')
                        score = horse.get('total_score', 0)
                        confidence = horse.get('confidence', 'N/A')
                        print(f"  {i}. {name}: {score:.1f}pts ({confidence})")
            else:
                print(f"D-Logic Calculation: NO DATA")
        else:
            print(f"Status: FAILED ({response.status_code})")
            print(f"Error: {response.text}")
            
    except Exception as e:
        test_results['chat_integration'] = False
        print(f"Error: {e}")
    
    # 5. 追加のチャットパターンテスト
    print("\n5. 追加チャットパターンテスト")
    print("-" * 30)
    chat_patterns = [
        "東京3Rの指数教えて",
        "3Rの指数を出して",
        "東京競馬場3レースのDロジック",
    ]
    
    pattern_results = []
    for pattern in chat_patterns:
        try:
            chat_request = {"message": pattern, "request_type": "d_logic"}
            response = client.post("/api/chat", json=chat_request)
            
            success = response.status_code == 200
            pattern_results.append(success)
            
            if success:
                data = response.json()
                print(f"Pattern '{pattern}': SUCCESS - {data.get('type', 'N/A')}")
            else:
                print(f"Pattern '{pattern}': FAILED - {response.status_code}")
                
        except Exception as e:
            pattern_results.append(False)
            print(f"Pattern '{pattern}': ERROR - {e}")
    
    test_results['chat_patterns'] = all(pattern_results)
    
    # 総合結果
    print("\n" + "=" * 60)
    print("PHASE C INTEGRATION TEST RESULTS")
    print("=" * 60)
    
    all_tests_passed = all(test_results.values())
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name.upper().replace('_', ' ')}: {status}")
    
    print(f"\nOVERALL PHASE C STATUS: {'🎉 PERFECT INTEGRATION' if all_tests_passed else '⚠️ NEEDS ATTENTION'}")
    
    if all_tests_passed:
        print("\n🚀 PHASE C: 本日レース統合・完璧ユーザー体験実装 COMPLETE!")
        print("📋 「本日の東京3Rの指数を出して」フロー完全動作")
        print("🎯 本日レースAPI + Dロジック連携 完璧統合")
        print("✨ 準備完了: フロントエンド統合・UI調整")
    else:
        print("\n🔧 Some Phase C features need attention")
    
    print("=" * 60)
    
    return all_tests_passed

if __name__ == "__main__":
    phase_c_integration_test()