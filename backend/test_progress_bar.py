#!/usr/bin/env python3
"""
ViewLogic履歴機能のプログレスバー表示テスト
"""

import asyncio
from services.v2.ai_handler import V2AIHandler

async def test_progress_bar():
    """プログレスバー表示のテスト"""
    
    print("🧪 ViewLogic履歴機能プログレスバーテスト")
    print("=" * 50)
    
    # テスト用レースデータ
    race_data = {
        'race_id': 'test-progress',
        'race_date': '2025-08-31',
        'venue': '新潟',
        'race_number': 11,
        'race_name': 'テストレース',
        'horses': ['ドウデュース', 'エフフォーリア', 'イクイノックス'],
        'jockeys': ['武豊', 'C.ルメール', '川田将雅'],
        'posts': [1, 2, 3],
        'horse_numbers': [1, 2, 3],
        'distance': '2000m',
        'track_condition': '良'
    }
    
    handler = V2AIHandler()
    handler.current_race_data = race_data
    
    # テストケース
    test_cases = [
        {
            'message': 'ドウデュースの過去データ',
            'description': '馬の過去データ取得'
        },
        {
            'message': '武豊騎手の過去データ',
            'description': '騎手の過去データ取得（フルネーム）'
        },
        {
            'message': '川田',
            'description': '騎手の過去データ取得（短縮名）'
        }
    ]
    
    for test in test_cases:
        print(f"\n🧪 {test['description']}")
        print(f"   メッセージ: '{test['message']}'")
        
        try:
            # AIタイプ判定
            ai_type, sub_type = handler.determine_ai_type(test['message'])
            print(f"   判定: {ai_type}/{sub_type}")
            
            if ai_type == 'viewlogic' and sub_type == 'history':
                # ViewLogicメッセージ処理
                content, result = await handler.process_viewlogic_message(
                    test['message'],
                    race_data,
                    sub_type
                )
                
                # プログレスメッセージが含まれているか確認
                if "ViewLogic過去データを取得中" in content:
                    print("   ✅ プログレスメッセージあり")
                    # 最初の数行を表示
                    lines = content.split('\n')
                    for i, line in enumerate(lines[:3]):
                        print(f"      {line}")
                else:
                    print("   ❌ プログレスメッセージなし")
                    print(f"      コンテンツ開始: {content[:100]}...")
            else:
                print(f"   ⚠️ ViewLogic履歴として判定されませんでした")
                
        except Exception as e:
            print(f"   ❌ エラー: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("テスト完了")

if __name__ == "__main__":
    asyncio.run(test_progress_bar())