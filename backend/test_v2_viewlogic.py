#!/usr/bin/env python3
"""
V2 API経由でViewLogic傾向分析をテスト
"""

import requests
import json
import uuid

def test_v2_viewlogic():
    """V2 API経由でViewLogicをテスト"""
    
    base_url = "http://localhost:8000/api/v2"
    
    # 1. まずチャットセッションを作成
    session_data = {
        "race_id": f"test-niigata-4r-{uuid.uuid4().hex[:8]}",
        "race_date": "2025-08-30",
        "venue": "新潟",
        "race_number": 4,
        "race_name": "テストレース",
        "horses": ["イージーブリージー", "エストゥペンダ", "ウンエン"],
        "jockeys": ["武豊", "川田", "ルメール"],
        "posts": [1, 2, 3],
        "distance": 1200,
        "course_type": "芝",
        "is_test_mode": True  # 管理者テストモード
    }
    
    print("1. チャットセッション作成...")
    response = requests.post(
        f"{base_url}/chat/create",
        json=session_data,
        headers={"x-user-id": "goldbenchan@gmail.com"}  # 管理者メール
    )
    
    if response.status_code != 200:
        print(f"❌ セッション作成失敗: {response.text}")
        return False
    
    session_info = response.json()
    session_id = session_info.get("session_id")
    print(f"✅ セッション作成成功: {session_id}")
    
    # 2. ViewLogic傾向分析メッセージを送信
    message_data = {
        "message": "傾向分析をして",
        "ai_type": "viewlogic"
    }
    
    print("\n2. ViewLogic傾向分析リクエスト送信...")
    response = requests.post(
        f"{base_url}/chat/{session_id}/message",
        json=message_data,
        headers={"x-user-id": "goldbenchan@gmail.com"}  # 管理者メール
    )
    
    if response.status_code != 200:
        print(f"❌ メッセージ送信失敗: {response.text}")
        return False
    
    result = response.json()
    
    # エラーチェック
    if "error" in result:
        print(f"❌ エラー発生: {result['error']}")
        return False
    
    print("✅ メッセージ送信成功")
    
    # 結果の表示
    content = result.get("content", "")
    print(f"\n応答内容（最初の500文字）:")
    print(content[:500])
    
    # 'int' object has no attribute 'get' エラーが出ないかチェック
    if "'int' object has no attribute 'get'" in content:
        print("\n❌ まだエラーが発生しています！")
        return False
    
    if "エラーが発生しました" in content:
        print("\n❌ ViewLogicエラーが発生しています")
        return False
    
    print("\n✅ ViewLogic傾向分析が正常に動作しています！")
    return True

if __name__ == "__main__":
    success = test_v2_viewlogic()
    if not success:
        print("\n問題が残っています")