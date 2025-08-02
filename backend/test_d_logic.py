#!/usr/bin/env python3
"""
D-Logic移植後の動作確認テスト
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(__file__))

from main import app
from fastapi.testclient import TestClient

def test_d_logic_migration():
    """D-Logic移植の動作確認"""
    client = TestClient(app)
    
    print("🧪 D-Logic移植後動作確認テスト")
    print("=" * 50)
    
    # 1. 基本ヘルスチェック
    print("\n1. 基本ヘルスチェック")
    response = client.get("/")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # 2. D-Logic状態確認
    print("\n2. D-Logic状態確認")
    response = client.get("/api/d-logic/status")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # 3. サンプルD-Logic計算
    print("\n3. サンプルD-Logic計算")
    response = client.get("/api/d-logic/sample")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"計算結果: {len(result.get('horses', []))}頭の分析完了")
        for horse in result.get('horses', [])[:3]:  # 上位3頭のみ表示
            print(f"  {horse.get('horse_name')}: {horse.get('total_score'):.1f}点")
    else:
        print(f"エラー: {response.text}")
    
    # 4. 本日レース情報
    print("\n4. 本日レース情報")
    response = client.get("/api/races/today")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"レース情報: {len(result.get('races', {}).get('tokyo', []))}レース（東京）")
    
    print("\n✅ D-Logic移植動作確認完了")
    print("🎯 本番環境（uma）でPhase B完了状態を確認")

if __name__ == "__main__":
    test_d_logic_migration()