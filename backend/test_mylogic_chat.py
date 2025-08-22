#!/usr/bin/env python3
"""
MyLogic chatエンドポイントのテスト
"""
import requests
import json

# ローカルサーバーのURL
BASE_URL = "http://localhost:8000"

def test_general_conversation():
    """一般的な会話のテスト"""
    print("=== 一般的な会話のテスト ===")
    
    test_messages = [
        "こんにちは",
        "MyLogicの使い方を教えてください",
        "重み付けの設定方法は？",
        "D-Logicとの違いは何ですか？",
        "ありがとう"
    ]
    
    for message in test_messages:
        print(f"\n質問: {message}")
        
        response = requests.post(
            f"{BASE_URL}/api/my-logic/chat",
            json={
                "message": message,
                "user_id": "test_user",
                "chat_history": []
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"応答: {data.get('response', 'No response')[:200]}...")
        else:
            print(f"エラー: {response.status_code}")
            print(response.text)

def test_horse_analysis():
    """馬名分析のテスト"""
    print("\n\n=== 馬名分析のテスト ===")
    
    test_messages = [
        "ドウデュース",
        "イクイノックス、ドウデュース",
        "エフフォーリアとジャスティンパレスを比較"
    ]
    
    for message in test_messages:
        print(f"\n分析: {message}")
        
        response = requests.post(
            f"{BASE_URL}/api/my-logic/chat",
            json={
                "message": message,
                "user_id": "test_user",
                "chat_history": []
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"結果: {data.get('response', 'No response')[:300]}...")
        else:
            print(f"エラー: {response.status_code}")
            print(response.text)

def test_chat_history():
    """チャット履歴を含むテスト"""
    print("\n\n=== チャット履歴のテスト ===")
    
    chat_history = [
        {"role": "user", "content": "こんにちは"},
        {"role": "assistant", "content": "こんにちは！MyLogic AIです。"}
    ]
    
    response = requests.post(
        f"{BASE_URL}/api/my-logic/chat",
        json={
            "message": "I-Logicについて教えて",
            "user_id": "test_user",
            "chat_history": chat_history
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"履歴付き応答: {data.get('response', 'No response')[:300]}...")
    else:
        print(f"エラー: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    print("MyLogic Chat API テスト開始\n")
    
    try:
        # サーバーの確認
        response = requests.get(f"{BASE_URL}/")
        print(f"サーバー状態: {response.status_code}")
    except:
        print("サーバーに接続できません。サーバーが起動していることを確認してください。")
        exit(1)
    
    test_general_conversation()
    test_horse_analysis()
    test_chat_history()
    
    print("\n\nテスト完了")