"""
レースアナリシス完全動作テスト
"""
import asyncio
from services.race_analysis_chat_handler import race_analysis_chat_handler

async def test_complete_race_analysis():
    """完全なレースアナリシスのテスト"""
    
    print("=== レースアナリシス完全動作テスト ===\n")
    
    # 札幌記念の分析要求（モックデータあり）
    message = "2025年8月18日の札幌記念を分析してください"
    
    print(f"テストメッセージ: '{message}'")
    print("-" * 60)
    
    # レースアナリシスリクエストの処理
    result = race_analysis_chat_handler.process_race_analysis_request(message)
    
    print(f"\n処理結果タイプ: {result.get('type')}")
    
    if result['type'] == 'race_analysis_result':
        print("\n✅ レース分析が成功しました！")
        print("\n=== 分析結果 ===")
        print(result['message'])
        
        # 生データも確認
        raw_data = result.get('raw_data', {})
        if raw_data:
            print("\n=== 生データ概要 ===")
            print(f"レース情報: {raw_data.get('race_info', {})}")
            print(f"分析結果数: {len(raw_data.get('results', []))}")
            print(f"基準馬: {raw_data.get('base_horse')}")
            print(f"分析タイプ: {raw_data.get('analysis_type')}")
    else:
        print(f"\n分析結果: {result.get('message')}")
    
    print("\n" + "=" * 60 + "\n")
    
    # 有馬記念のテスト（過去G1レース）
    message2 = "2024年の有馬記念を分析して"
    
    print(f"テストメッセージ2: '{message2}'")
    print("-" * 60)
    
    result2 = race_analysis_chat_handler.process_race_analysis_request(message2)
    
    print(f"\n処理結果タイプ: {result2.get('type')}")
    
    if result2['type'] == 'race_analysis_result':
        print("\n✅ 有馬記念の分析も成功しました！")
        # 結果の一部のみ表示
        lines = result2['message'].split('\n')
        print('\n'.join(lines[:20]))  # 最初の20行のみ
        print("... (以下省略)")
    else:
        print(f"\n分析結果: {result2.get('message')}")

if __name__ == "__main__":
    asyncio.run(test_complete_race_analysis())