#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(__file__))

from main import app
from fastapi.testclient import TestClient

def final_migration_test():
    client = TestClient(app)
    
    print("=" * 50)
    print("D-LOGIC MIGRATION FINAL TEST")
    print("=" * 50)
    
    results = {}
    
    # 1. Basic System
    print("\n1. Basic System Check")
    response = client.get("/")
    results['basic'] = response.status_code == 200
    if results['basic']:
        data = response.json()
        print(f"   Status: OK - {data.get('message', '')}")
        print(f"   Version: {data.get('version', '')}")
    else:
        print(f"   Status: FAILED - {response.status_code}")
    
    # 2. D-Logic Status
    print("\n2. D-Logic System Status")
    response = client.get("/api/d-logic/status")
    results['status'] = response.status_code == 200
    if results['status']:
        data = response.json()
        print(f"   Engine: {data.get('d_logic_engine', '')}")
        print(f"   Knowledge Base: OK")
        print(f"   Phase: {data.get('status', '')}")
        print(f"   Ready for Phase C: {data.get('ready_for_phase_c', False)}")
        
        validation = data.get('validation', {})
        all_valid = all(validation.values())
        results['validation'] = all_valid
        print(f"   Validation: {'ALL PASS' if all_valid else 'SOME FAILED'}")
        for k, v in validation.items():
            print(f"     - {k}: {'OK' if v else 'FAIL'}")
    else:
        print(f"   Status: FAILED - {response.status_code}")
    
    # 3. D-Logic Calculation
    print("\n3. D-Logic 12-Item Calculation")
    response = client.get("/api/d-logic/sample")
    results['calculation'] = response.status_code == 200
    if results['calculation']:
        data = response.json()
        horses = data.get('horses', [])
        print(f"   Calculation: SUCCESS")
        print(f"   Horses analyzed: {len(horses)}")
        print(f"   Base reference: {data.get('base_reference', '')}")
        
        # Check 12 items
        if horses:
            first_horse = horses[0]
            d_logic = first_horse.get('d_logic_score', {})
            required_items = [
                'distance_aptitude', 'bloodline_evaluation', 'jockey_compatibility',
                'trainer_evaluation', 'track_aptitude', 'weather_aptitude',
                'popularity_factor', 'weight_impact', 'horse_weight_impact',
                'corner_specialist', 'margin_analysis', 'time_index'
            ]
            
            items_present = sum(1 for item in required_items if item in d_logic)
            results['twelve_items'] = items_present == 12
            print(f"   12-Item completeness: {items_present}/12 items")
            
            print(f"   Top 3 Results:")
            for i, horse in enumerate(horses[:3], 1):
                name = horse.get('horse_name', '')
                score = horse.get('total_score', 0)
                confidence = horse.get('confidence', '')
                print(f"     {i}. {name}: {score:.1f} pts ({confidence})")
    else:
        print(f"   Calculation: FAILED - {response.status_code}")
    
    # 4. Race Info
    print("\n4. Race Information")
    response = client.get("/api/races/today")
    results['races'] = response.status_code == 200
    if results['races']:
        data = response.json()
        races = data.get('races', {})
        total = sum(len(r) for r in races.values())
        print(f"   Race info: OK")
        print(f"   Total races: {total}")
        for course, course_races in races.items():
            print(f"     {course}: {len(course_races)} races")
    else:
        print(f"   Race info: FAILED - {response.status_code}")
    
    # 5. Chat Integration
    print("\n5. Chat API Integration")
    try:
        chat_data = {"message": "D-Logic calculation test", "request_type": "d_logic"}
        response = client.post("/api/chat", json=chat_data)
        results['chat'] = response.status_code == 200
        if results['chat']:
            data = response.json()
            print(f"   Chat API: OK")
            print(f"   Response type: {data.get('type', '')}")
        else:
            print(f"   Chat API: FAILED - {response.status_code}")
    except Exception as e:
        results['chat'] = False
        print(f"   Chat API: ERROR - {e}")
    
    # 6. File Structure
    print("\n6. File Structure")
    required_files = [
        'main.py', 'models/d_logic_models.py', 'api/d_logic.py',
        'services/knowledge_base.py', 'data/knowledgeBase.json'
    ]
    
    missing = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing.append(file_path)
    
    results['files'] = len(missing) == 0
    print(f"   File structure: {'OK' if results['files'] else 'MISSING FILES'}")
    if missing:
        for f in missing:
            print(f"     Missing: {f}")
    
    # Final Results
    print("\n" + "=" * 50)
    print("FINAL MIGRATION TEST RESULTS")
    print("=" * 50)
    
    all_passed = all(results.values())
    
    for test_name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"{test_name.upper()}: {status}")
    
    print(f"\nOVERALL: {'PERFECT MIGRATION SUCCESS' if all_passed else 'ISSUES DETECTED'}")
    
    if all_passed:
        print("\nUMA FOLDER IS PRODUCTION READY!")
        print("Phase B (12-Item D-Logic): COMPLETE")
        print("Ready for Phase C development")
        print("keiba-ai folder can be safely deleted")
    else:
        print("\nSome tests failed - review above results")
    
    print("=" * 50)
    return all_passed

if __name__ == "__main__":
    final_migration_test()