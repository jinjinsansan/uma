#!/usr/bin/env python3
"""
D-Logic移植完全性確認テスト
umaフォルダに完璧に移植されているかを詳細確認
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from main import app
from fastapi.testclient import TestClient
import json

def comprehensive_d_logic_test():
    """D-Logic移植の完全性を詳細確認"""
    client = TestClient(app)
    
    print("=" * 60)
    print("D-LOGIC MIGRATION COMPREHENSIVE TEST")
    print("=" * 60)
    
    test_results = {}
    
    # 1. 基本システム確認
    print("\n1. BASIC SYSTEM CHECK")
    print("-" * 30)
    try:
        response = client.get("/")
        test_results['basic_health'] = response.status_code == 200
        result = response.json()
        print(f"Status: {response.status_code}")
        print(f"Title: {result.get('message', 'N/A')}")
        print(f"Version: {result.get('version', 'N/A')}")
        print(f"✅ Basic health: {'PASS' if test_results['basic_health'] else 'FAIL'}")
    except Exception as e:
        test_results['basic_health'] = False
        print(f"❌ Basic health: FAIL - {e}")
    
    # 2. D-Logic システム状態確認
    print("\n2. D-LOGIC SYSTEM STATUS")
    print("-" * 30)
    try:
        response = client.get("/api/d-logic/status")
        test_results['d_logic_status'] = response.status_code == 200
        result = response.json()
        print(f"Status: {response.status_code}")
        print(f"D-Logic Engine: {result.get('d_logic_engine', 'N/A')}")
        print(f"Knowledge Base: {result.get('knowledge_base', 'N/A')}")
        print(f"Phase Status: {result.get('status', 'N/A')}")
        print(f"Ready for Phase C: {result.get('ready_for_phase_c', False)}")
        
        # Validation check
        validation = result.get('validation', {})
        all_valid = all(validation.values()) if validation else False
        test_results['validation'] = all_valid
        print(f"Validation Results:")
        for key, value in validation.items():
            print(f"  - {key}: {'✅' if value else '❌'}")
        
        print(f"✅ D-Logic status: {'PASS' if test_results['d_logic_status'] and all_valid else 'FAIL'}")
    except Exception as e:
        test_results['d_logic_status'] = False
        print(f"❌ D-Logic status: FAIL - {e}")
    
    # 3. 12項目D-Logic計算エンジンテスト
    print("\n3. 12-ITEM D-LOGIC CALCULATION ENGINE")
    print("-" * 30)
    try:
        response = client.get("/api/d-logic/sample")
        test_results['d_logic_calculation'] = response.status_code == 200
        
        if response.status_code == 200:
            result = response.json()
            horses = result.get('horses', [])
            print(f"Calculation Status: SUCCESS")
            print(f"Horses Analyzed: {len(horses)}")
            print(f"Base Reference: {result.get('base_reference', 'N/A')}")
            print(f"Calculation Time: {result.get('calculation_time', 'N/A')}")
            
            print(f"Top 3 Results:")
            for i, horse in enumerate(horses[:3], 1):
                horse_name = horse.get('horse_name', 'N/A')
                total_score = horse.get('total_score', 0)
                confidence = horse.get('confidence', 'N/A')
                rank = horse.get('rank', i)
                
                print(f"  {rank}. {horse_name}: {total_score:.1f}pts (confidence: {confidence})")
                
                # 12項目詳細確認
                d_logic_score = horse.get('d_logic_score', {})
                if d_logic_score:
                    print(f"     12-Item Breakdown:")
                    items = [
                        'distance_aptitude', 'bloodline_evaluation', 'jockey_compatibility',
                        'trainer_evaluation', 'track_aptitude', 'weather_aptitude',
                        'popularity_factor', 'weight_impact', 'horse_weight_impact',
                        'corner_specialist', 'margin_analysis', 'time_index'
                    ]
                    for item in items[:6]:  # Show first 6 items
                        value = d_logic_score.get(item, 0)
                        print(f"       {item}: {value:.1f}")
                    print(f"       ... (and 6 more items)")
            
            # 12項目すべてが存在するかチェック
            first_horse = horses[0] if horses else {}
            d_logic_score = first_horse.get('d_logic_score', {})
            required_items = [
                'distance_aptitude', 'bloodline_evaluation', 'jockey_compatibility',
                'trainer_evaluation', 'track_aptitude', 'weather_aptitude',
                'popularity_factor', 'weight_impact', 'horse_weight_impact',
                'corner_specialist', 'margin_analysis', 'time_index'
            ]
            
            all_items_present = all(item in d_logic_score for item in required_items)
            test_results['twelve_items'] = all_items_present
            
            print(f"12-Item Completeness: {'✅ ALL 12 ITEMS PRESENT' if all_items_present else '❌ MISSING ITEMS'}")
            
        else:
            print(f"❌ Calculation failed: {response.status_code}")
            print(f"Error: {response.text}")
        
        print(f"✅ D-Logic calculation: {'PASS' if test_results['d_logic_calculation'] else 'FAIL'}")
        
    except Exception as e:
        test_results['d_logic_calculation'] = False
        print(f"❌ D-Logic calculation: FAIL - {e}")
    
    # 4. レース情報API確認
    print("\n4. RACE INFORMATION API")
    print("-" * 30)
    try:
        response = client.get("/api/races/today")
        test_results['race_info'] = response.status_code == 200
        
        if response.status_code == 200:
            result = response.json()
            races = result.get('races', {})
            total_races = sum(len(course_races) for course_races in races.values())
            print(f"Race Info Status: SUCCESS")
            print(f"Total Races Available: {total_races}")
            for course, course_races in races.items():
                print(f"  {course.upper()}: {len(course_races)} races")
        
        print(f"✅ Race info: {'PASS' if test_results['race_info'] else 'FAIL'}")
        
    except Exception as e:
        test_results['race_info'] = False
        print(f"❌ Race info: FAIL - {e}")
    
    # 5. チャットAPI確認
    print("\n5. CHAT API WITH D-LOGIC INTEGRATION")
    print("-" * 30)
    try:
        # Test chat request
        chat_request = {
            "message": "東京3Rの指数を出して",
            "request_type": "d_logic"
        }
        response = client.post("/api/chat", json=chat_request)
        test_results['chat_integration'] = response.status_code == 200
        
        if response.status_code == 200:
            result = response.json()
            print(f"Chat Status: SUCCESS")
            print(f"Response Type: {result.get('type', 'N/A')}")
            print(f"Message Preview: {result.get('message', 'N/A')[:100]}...")
            print(f"D-Logic Button: {result.get('show_d_logic_button', False)}")
        
        print(f"✅ Chat integration: {'PASS' if test_results['chat_integration'] else 'FAIL'}")
        
    except Exception as e:
        test_results['chat_integration'] = False
        print(f"❌ Chat integration: FAIL - {e}")
    
    # 6. ファイル構造確認
    print("\n6. FILE STRUCTURE VERIFICATION")
    print("-" * 30)
    required_files = [
        'main.py',
        'models/d_logic_models.py',
        'api/d_logic.py',
        'services/knowledge_base.py',
        'data/knowledgeBase.json',
        'frontend/src/data/knowledgeBase.json'
    ]
    
    file_check = {}
    for file_path in required_files:
        full_path = os.path.join(os.path.dirname(__file__), '..', file_path)
        exists = os.path.exists(full_path)
        file_check[file_path] = exists
        print(f"  {file_path}: {'✅' if exists else '❌'}")
    
    test_results['file_structure'] = all(file_check.values())
    print(f"✅ File structure: {'PASS' if test_results['file_structure'] else 'FAIL'}")
    
    # 総合結果
    print("\n" + "=" * 60)
    print("COMPREHENSIVE TEST RESULTS")
    print("=" * 60)
    
    all_tests_passed = all(test_results.values())
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name.upper().replace('_', ' ')}: {status}")
    
    print(f"\nOVERALL MIGRATION STATUS: {'🎉 PERFECT MIGRATION' if all_tests_passed else '⚠️  NEEDS ATTENTION'}")
    
    if all_tests_passed:
        print("\n🚀 UMA FOLDER IS READY FOR PRODUCTION!")
        print("📋 Phase B (12-Item D-Logic): COMPLETE")
        print("🎯 Ready for Phase C development")
    else:
        print("\n🔧 Some issues detected - please review failed tests")
    
    print("=" * 60)
    
    return all_tests_passed

if __name__ == "__main__":
    comprehensive_d_logic_test()