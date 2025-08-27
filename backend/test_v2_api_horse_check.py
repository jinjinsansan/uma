#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V2 API エンドポイント経由での馬名チェックテスト
"""

import requests
import json
import time

def test_api_horse_check():
    """API経由での馬名チェックテスト"""
    
    # APIベースURL (ローカルテスト用)
    base_url = "http://localhost:8000/api/v2"
    
    # テスト用のメールヘッダー
    headers = {
        "X-User-Email": "test@example.com",
        "Content-Type": "application/json"
    }
    
    # まずチャットセッションを作成
    print("=== チャットセッション作成 ===")
    create_data = {
        "race_id": "test-niigata-6r-20250827",
        "race_date": "2025-08-27",
        "venue": "新潟",
        "race_number": 6,
        "race_name": "テストレース",
        "horses": [
            "ドウデュース",
            "イクイノックス",
            "エフフォーリア",
            "ジャスティンパレス",
            "タイトルホルダー"
        ],
        "jockeys": ["武豊", "C.ルメール", "川田将雅", "横山和生", "横山武史"],
        "posts": [1, 2, 3, 4, 5],
        "horse_numbers": [1, 2, 3, 4, 5]
    }
    
    try:
        response = requests.post(
            f"{base_url}/chat/create",
            headers=headers,
            json=create_data
        )
        
        if response.status_code == 200:
            result = response.json()
            chat_id = result.get('chat_id')
            print(f"チャットID: {chat_id}")
            print(f"残ポイント: {result.get('remaining_points')}")
        else:
            print(f"エラー: {response.status_code}")
            print(response.text)
            return
            
    except Exception as e:
        print(f"接続エラー: {e}")
        print("ローカルサーバーが起動していることを確認してください")
        return
    
    # テストケース実行
    test_cases = [
        {
            "name": "レースに存在する馬",
            "message": "ドウデュースの分析をして",
            "expected": "正常な分析結果"
        },
        {
            "name": "レースに存在しない馬",
            "message": "コントレイルの分析をして",
            "expected": "出走しませんメッセージ"
        },
        {
            "name": "複数の馬（一部存在しない）",
            "message": "ドウデュースとアーモンドアイを比較して",
            "expected": "出走しませんメッセージ"
        },
        {
            "name": "他のレースへの言及",
            "message": "東京11Rの分析をして",
            "expected": "専用チャットメッセージ"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n=== テストケース{i}: {test_case['name']} ===")
        print(f"メッセージ: {test_case['message']}")
        
        try:
            response = requests.post(
                f"{base_url}/chat/session/{chat_id}/message",
                headers=headers,
                json={
                    "message": test_case['message'],
                    "ai_type": "imlogic"
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result.get('message', {}).get('content', '')
                print(f"応答: {content[:200]}...")  # 最初の200文字のみ表示
                
                # エラーメッセージのチェック
                if "出走しません" in content:
                    print("✅ 正しく馬名チェックエラーを検出")
                elif "専用です" in content:
                    print("✅ 正しくレース範囲外エラーを検出")
                else:
                    print("📊 正常な分析結果を返却")
                    
            else:
                print(f"❌ APIエラー: {response.status_code}")
                error_data = response.json()
                print(f"詳細: {error_data.get('detail', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ リクエストエラー: {e}")
        
        time.sleep(1)  # レート制限対策

if __name__ == "__main__":
    print("V2 API 馬名チェック統合テスト")
    print("=" * 50)
    print("\n注意: このテストを実行する前に、バックエンドサーバーを起動してください:")
    print("cd /chatbot/uma/backend && uvicorn main:app --reload --port 8000")
    print()
    
    test_api_horse_check()
    print("\n統合テスト完了")