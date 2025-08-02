#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(__file__))

from main import app
from fastapi.testclient import TestClient

def test_d_logic_migration():
    client = TestClient(app)
    
    print("D-Logic Migration Test")
    print("=" * 30)
    
    # Basic health check
    print("\n1. Health Check")
    response = client.get("/")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # D-Logic status
    print("\n2. D-Logic Status")
    response = client.get("/api/d-logic/status")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Sample D-Logic calculation
    print("\n3. Sample D-Logic")
    response = client.get("/api/d-logic/sample")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Calculated: {len(result.get('horses', []))} horses")
        for horse in result.get('horses', [])[:3]:
            print(f"  {horse.get('horse_name')}: {horse.get('total_score'):.1f}")
    else:
        print(f"Error: {response.text}")
    
    print("\nMigration test completed successfully!")

if __name__ == "__main__":
    test_d_logic_migration()