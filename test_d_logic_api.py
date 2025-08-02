import requests
import json

def test_d_logic_api():
    """DロジックAPIテスト"""
    
    # テストデータ
    test_data = {
        "race_code": "test001",
        "horses": [
            {
                "horse_id": "001",
                "horse_name": "テスト馬1",
                "jockey_name": "武豊",
                "trainer_name": "テスト調教師1",
                "weight": 55.0,
                "weight_change": 0.0
            },
            {
                "horse_id": "002",
                "horse_name": "テスト馬2",
                "jockey_name": "テスト騎手2",
                "trainer_name": "テスト調教師2",
                "weight": 54.5,
                "weight_change": -0.5
            }
        ]
    }
    
    try:
        # 健全性チェック
        print("1. 健全性チェック...")
        health_response = requests.get("http://localhost:8000/api/d-logic/health")
        print(f"   結果: {health_response.status_code} - {health_response.json()}")
        
        # Dロジック計算
        print("\n2. Dロジック計算...")
        calc_response = requests.post(
            "http://localhost:8000/api/d-logic/calculate",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        if calc_response.status_code == 200:
            result = calc_response.json()
            print(f"   結果: {calc_response.status_code}")
            print(f"   計算方法: {result.get('calculation_method')}")
            print(f"   基準馬: {result.get('base_horse')}")
            print(f"   基準スコア: {result.get('base_score')}")
            print(f"   SQL活用: {result.get('sql_data_utilization')}")
            print(f"   出走頭数: {result.get('calculation_summary', {}).get('total_horses')}")
            
            # 馬別結果
            horses = result.get('horses', [])
            print(f"\n   馬別結果:")
            for i, horse in enumerate(horses):
                print(f"   {i+1}位: {horse['horse_name']} - {horse['d_logic_score']:.1f}点")
                
        else:
            print(f"   エラー: {calc_response.status_code} - {calc_response.text}")
        
        # ナレッジベース取得
        print("\n3. ナレッジベース取得...")
        kb_response = requests.get("http://localhost:8000/api/d-logic/knowledge-base")
        if kb_response.status_code == 200:
            kb_data = kb_response.json()
            print(f"   結果: {kb_response.status_code}")
            print(f"   基準馬データ: 取得済み")
            print(f"   SQL評価基準: 取得済み")
            print(f"   Dロジック重み: 取得済み")
        else:
            print(f"   エラー: {kb_response.status_code} - {kb_response.text}")
            
    except Exception as e:
        print(f"エラー: {e}")

if __name__ == "__main__":
    test_d_logic_api() 