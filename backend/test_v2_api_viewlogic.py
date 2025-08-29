#!/usr/bin/env python3
"""
V2 API エンドポイントでのViewLogicテスト
実際のHTTPリクエストをシミュレート
"""

import sys
import os
import json
import asyncio
from datetime import datetime

# プロジェクトのルートディレクトリをPythonパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# FastAPIアプリケーションをインポート
from main import app
from fastapi.testclient import TestClient


def print_section(title):
    """セクションタイトルを表示"""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)


def test_viewlogic_api():
    """V2 APIエンドポイントでViewLogicをテスト"""
    
    client = TestClient(app)
    
    print_section("V2 API ViewLogicテスト")
    
    # テスト用のセッションID
    test_session_id = f"test_session_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # テスト用のレースデータ
    race_data = {
        "venue": "東京",
        "race_number": 11,
        "race_name": "天皇賞（秋）",
        "distance": 2000,
        "horses": [
            "ドウデュース",
            "イクイノックス",
            "ジャスティンパレス",
            "ノースブリッジ",
            "サリエラ"
        ]
    }
    
    # 1. チャットセッション作成
    print("\n1. チャットセッション作成")
    response = client.post(
        "/api/v2/chat/create",
        json={
            "race_id": "test_race_001",
            "race_date": datetime.now().strftime("%Y-%m-%d"),
            **race_data,
            "is_test_mode": True  # テストモードでポイント消費なし
        },
        headers={"X-User-Email": "test@example.com"}
    )
    
    if response.status_code == 200:
        session_data = response.json()
        session_id = session_data.get("session_id")
        print(f"✅ セッション作成成功: {session_id}")
    else:
        print(f"❌ セッション作成失敗: {response.status_code}")
        print(response.text)
        return
    
    # 2. ViewLogic展開予想テスト
    print("\n2. ViewLogic展開予想テスト")
    test_messages = [
        ("展開予想をしてください", "viewlogic", "flow"),
        ("東京2000mの傾向を教えて", "viewlogic", "trend"),
        ("今日の見解をお願いします", "viewlogic", "opinion")
    ]
    
    for message_text, expected_ai, expected_sub in test_messages:
        print(f"\n📝 メッセージ: 「{message_text}」")
        
        response = client.post(
            f"/api/v2/chat/session/{session_id}/message",
            json={
                "message": message_text,
                "ai_type": None  # 自動判定
            },
            headers={"X-User-Email": "test@example.com"}
        )
        
        if response.status_code == 200:
            result = response.json()
            message_data = result.get("message", {})
            
            # AI タイプの確認
            ai_type = message_data.get("ai_type", "unknown")
            sub_type = message_data.get("sub_type", "unknown")
            
            if ai_type == expected_ai:
                print(f"✅ AI判定成功: {ai_type}/{sub_type}")
            else:
                print(f"❌ AI判定失敗: 期待={expected_ai}, 実際={ai_type}")
            
            # 応答内容の表示（最初の200文字）
            content = message_data.get("content", "")
            print(f"応答内容（抜粋）:")
            print(content[:200] + "..." if len(content) > 200 else content)
            
        else:
            print(f"❌ API呼び出し失敗: {response.status_code}")
            print(response.text)
    
    # 3. セッション履歴の確認
    print("\n3. セッション履歴の確認")
    response = client.get(
        f"/api/v2/chat/sessions",
        headers={"X-User-Email": "test@example.com"}
    )
    
    if response.status_code == 200:
        sessions = response.json()
        if sessions and len(sessions) > 0:
            print(f"✅ セッション取得成功: {len(sessions)}件")
            # 最新のセッションを確認
            latest = sessions[0]
            print(f"   最新セッション: {latest.get('id')}")
            print(f"   メッセージ数: {latest.get('message_count', 0)}")
        else:
            print("セッションが見つかりません")
    else:
        print(f"❌ セッション取得失敗: {response.status_code}")


def test_error_handling():
    """エラーハンドリングのテスト"""
    print_section("エラーハンドリングテスト")
    
    client = TestClient(app)
    
    # 存在しないセッションへのメッセージ送信
    print("\n1. 存在しないセッションへのメッセージ送信")
    response = client.post(
        "/api/v2/chat/session/invalid_session_id/message",
        json={
            "message": "テストメッセージ",
            "ai_type": None
        },
        headers={"X-User-Email": "test@example.com"}
    )
    
    if response.status_code != 200:
        print(f"✅ 期待通りのエラー: {response.status_code}")
    else:
        print("❌ エラーが期待されたが成功してしまった")
    
    # 空の馬リストでセッション作成
    print("\n2. 空の馬リストでセッション作成")
    response = client.post(
        "/api/v2/chat/create",
        json={
            "race_id": "test_empty_race",
            "race_date": datetime.now().strftime("%Y-%m-%d"),
            "venue": "東京",
            "race_number": 1,
            "race_name": "テストレース",
            "horses": [],  # 空のリスト
            "is_test_mode": True
        },
        headers={"X-User-Email": "test@example.com"}
    )
    
    if response.status_code == 200:
        print("✅ 空の馬リストでもセッション作成成功")
    else:
        print(f"セッション作成失敗: {response.status_code}")


def main():
    """メイン実行関数"""
    print("\n" + "🏇"*30)
    print("  V2 API ViewLogic統合テスト")
    print("🏇"*30)
    
    try:
        test_viewlogic_api()
        test_error_handling()
        
        print("\n" + "="*60)
        print(" APIテスト完了")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ テスト中にエラーが発生: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()