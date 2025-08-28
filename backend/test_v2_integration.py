#!/usr/bin/env python3
"""
V2システム統合テスト
自然言語AI切り替え機能の完全な動作確認
"""
import asyncio
import json
from datetime import datetime
import os
import sys

# パスを追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 環境変数設定（テスト用）
os.environ['SUPABASE_URL'] = 'https://veklxmosegqkjtvjbksd.supabase.co'
os.environ['ANTHROPIC_API_KEY'] = os.environ.get('ANTHROPIC_API_KEY', 'mock-key-for-testing')

def print_header(title):
    """ヘッダーを表示"""
    print("\n" + "=" * 50)
    print(f" {title}")
    print("=" * 50)

def print_result(message, result):
    """テスト結果を表示"""
    status = "✅" if result else "❌"
    print(f"{status} {message}")

async def test_ai_handler():
    """AIハンドラーの直接テスト"""
    print_header("1. AIハンドラー直接テスト")
    
    from services.v2.ai_handler import V2AIHandler
    handler = V2AIHandler()
    
    # テスト用レースデータ
    race_data = {
        'race_id': 'test_race_1',
        'venue': '東京',
        'race_number': 11,
        'race_name': '天皇賞（秋）',
        'horses': ['イクイノックス', 'ドウデュース', 'ジャックドール'],
        'jockeys': ['C.ルメール', '武豊', '藤田菜七子'],
        'posts': [1, 2, 3],
        'horse_numbers': [1, 2, 3]
    }
    
    # テストケース
    test_cases = [
        ("このレースを分析して", "imlogic"),
        ("D-Logicで評価して", "dlogic"),
        ("I-Logic分析をお願い", "ilogic"),
        ("D-Logic指数を教えて", "dlogic"),
        ("レースアナリシスして", "ilogic"),
    ]
    
    for message, expected_ai in test_cases:
        print(f"\nテスト: '{message}'")
        result = await handler.process_message(
            message=message,
            race_data=race_data
        )
        
        actual_ai = result.get('ai_type', '')
        is_correct = actual_ai == expected_ai
        print_result(f"期待: {expected_ai}, 実際: {actual_ai}", is_correct)
        
        # 結果の一部を表示
        content = result.get('content', '')
        if content:
            preview = content[:100] + "..." if len(content) > 100 else content
            print(f"  応答プレビュー: {preview}")

async def test_chat_session_creation():
    """チャットセッション作成のテスト"""
    print_header("2. チャットセッション作成テスト")
    
    from services.v2.chat_service import V2ChatService
    service = V2ChatService()
    
    # テスト用ユーザー
    test_user_id = "test-user-" + datetime.now().strftime("%Y%m%d%H%M%S")
    
    # セッション作成
    session = await service.create_session(
        user_id=test_user_id,
        race_id="test_race_1",
        race_date="2025-01-28",
        venue="東京",
        race_number=11,
        race_name="天皇賞（秋）",
        horses=['イクイノックス', 'ドウデュース'],
        jockeys=['C.ルメール', '武豊'],
        posts=[1, 2],
        horse_numbers=[1, 2]
    )
    
    if session:
        print_result(f"セッション作成成功: {session.get('id', 'N/A')}", True)
        return session
    else:
        print_result("セッション作成失敗", False)
        return None

async def test_message_flow(session):
    """メッセージフローのテスト"""
    if not session:
        print("セッションがないためスキップ")
        return
    
    print_header("3. メッセージフローテスト")
    
    from services.v2.chat_service import V2ChatService
    from services.v2.ai_handler import V2AIHandler
    
    service = V2ChatService()
    handler = V2AIHandler()
    
    # セッションIDと情報を取得
    session_id = session.get('id')
    
    # レースデータを構築
    race_data = {
        'race_id': session.get('race_id'),
        'venue': session.get('venue'),
        'race_number': session.get('race_number'),
        'race_name': session.get('race_name'),
        'horses': session.get('horses', []),
        'jockeys': session.get('jockeys', []),
        'posts': session.get('posts', []),
        'horse_numbers': session.get('horse_numbers', [])
    }
    
    # テストメッセージ
    test_messages = [
        "このレースをIMLogicで分析して",
        "D-Logic指数も見せて",
        "I-Logicではどう？"
    ]
    
    for msg in test_messages:
        print(f"\nメッセージ送信: '{msg}'")
        
        # AIハンドラーで処理
        ai_response = await handler.process_message(
            message=msg,
            race_data=race_data
        )
        
        # メッセージ保存
        user_msg = await service.save_message(
            session_id=session_id,
            role="user",
            content=msg,
            ai_type="imlogic"  # デフォルト
        )
        
        assistant_msg = await service.save_message(
            session_id=session_id,
            role="assistant",
            content=ai_response.get("content", ""),
            ai_type=ai_response.get("ai_type", "imlogic")
        )
        
        if user_msg and assistant_msg:
            print_result(f"AI: {ai_response.get('ai_type', 'unknown')}", True)
        else:
            print_result("メッセージ保存失敗", False)

async def test_natural_language_switching():
    """自然言語によるAI切り替えの詳細テスト"""
    print_header("4. 自然言語AI切り替え詳細テスト")
    
    from services.v2.ai_handler import V2AIHandler
    handler = V2AIHandler()
    
    # 簡易レースデータ
    race_data = {
        'venue': '中山',
        'race_number': 9,
        'horses': ['テストホース'],
        'jockeys': ['テスト騎手'],
        'posts': [1],
        'horse_numbers': [1]
    }
    
    # 詳細なテストケース
    test_patterns = [
        # IMLogic
        ("分析して", "imlogic"),
        ("評価をお願い", "imlogic"),
        ("このレースどう？", "imlogic"),
        
        # D-Logic
        ("D-Logicで分析", "dlogic"),
        ("ディーロジックの指数", "dlogic"),
        ("12項目評価して", "dlogic"),
        
        # I-Logic
        ("I-Logicで見て", "ilogic"),
        ("アイロジック分析", "ilogic"),
        ("レースアナリシスをお願い", "ilogic"),
        ("騎手も含めて評価", "ilogic"),
        
        # ViewLogic
        ("傾向を教えて", "viewlogic"),
        ("トレンドは？", "viewlogic"),
        ("見解を聞かせて", "viewlogic"),
    ]
    
    success_count = 0
    total_count = len(test_patterns)
    
    for message, expected_ai in test_patterns:
        result = await handler.process_message(
            message=message,
            race_data=race_data
        )
        
        actual_ai = result.get('ai_type', '')
        is_correct = actual_ai == expected_ai
        
        if is_correct:
            success_count += 1
            print(f"✅ '{message}' -> {actual_ai}")
        else:
            print(f"❌ '{message}' -> 期待: {expected_ai}, 実際: {actual_ai}")
    
    print(f"\n成功率: {success_count}/{total_count} ({success_count*100//total_count}%)")

async def main():
    """メインテスト実行"""
    print("\n" + "=" * 50)
    print(" V2システム統合テスト")
    print(" 自然言語AI切り替え機能")
    print("=" * 50)
    
    try:
        # 1. AIハンドラー直接テスト
        await test_ai_handler()
        
        # 2. チャットセッション作成
        session = await test_chat_session_creation()
        
        # 3. メッセージフロー
        await test_message_flow(session)
        
        # 4. 自然言語切り替え詳細
        await test_natural_language_switching()
        
        print("\n" + "=" * 50)
        print(" テスト完了")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n❌ エラー発生: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())