#!/usr/bin/env python3
"""
アーカイブレース認識機能のテスト
"""
import asyncio
from services.archive_race_handler import archive_race_handler

async def test_archive_recognition():
    """アーカイブレース認識のテスト"""
    print("=== アーカイブレース認識テスト ===\n")
    
    # テストケース
    test_messages = [
        "新潟7R分析して",
        "札幌記念を分析して",
        "8月16日の新潟7Rを分析して",
        "昨日の中京6Rはどうでしたか",
        "札幌11Rの分析をお願いします",
        "普通のメッセージです",
        "ドウデュースの分析をして"
    ]
    
    for message in test_messages:
        print(f"\nメッセージ: '{message}'")
        print("-" * 50)
        
        # レース情報を抽出
        race_info = archive_race_handler.extract_race_info(message)
        
        if race_info:
            print(f"✅ レース情報を検出:")
            print(f"   開催場: {race_info.get('venue', '未指定')}")
            print(f"   レース番号: {race_info.get('race_number', '未指定')}")
            print(f"   日付: {race_info.get('date', '未指定')}")
            print(f"   レース名: {race_info.get('race_name', '未指定')}")
            print(f"   アクション: {race_info.get('action', '未指定')}")
            
            # アーカイブレースを検索
            if race_info.get('action') == 'analyze':
                search_result = await archive_race_handler.search_archive_races(race_info)
                print(f"\n📚 アーカイブ検索結果:")
                print(f"   見つかった: {search_result['found']}")
                print(f"   候補数: {search_result['count']}")
                
                if search_result['matches']:
                    print(f"   候補:")
                    for match in search_result['matches']:
                        print(f"     - {match['date']} {match['venue']}{match['race_number']}R「{match['race_name']}」")
                
                if search_result['need_selection']:
                    print(f"\n   ⚠️ 複数候補があるため選択が必要です")
                    selection_msg = archive_race_handler.format_selection_message(search_result['matches'])
                    print(f"\n選択メッセージ:\n{selection_msg}")
        else:
            print(f"❌ レース情報は検出されませんでした")

async def test_multiple_matches():
    """複数候補がある場合のテスト"""
    print("\n\n=== 複数候補テスト ===\n")
    
    # 開催場のみ指定（複数候補になるはず）
    message = "新潟のレースを分析して"
    print(f"メッセージ: '{message}'")
    
    race_info = archive_race_handler.extract_race_info(message)
    if race_info:
        search_result = await archive_race_handler.search_archive_races(race_info)
        
        if search_result['need_selection']:
            print("\n複数候補の選択画面:")
            print(archive_race_handler.format_selection_message(search_result['matches']))

if __name__ == "__main__":
    asyncio.run(test_archive_recognition())
    asyncio.run(test_multiple_matches())