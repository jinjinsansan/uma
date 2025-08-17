"""
レースアナリシスチャット機能のテスト
"""
import asyncio
from services.race_analysis_chat_handler import race_analysis_chat_handler

async def test_race_analysis():
    """レースアナリシスのテスト"""
    
    # テストケース
    test_messages = [
        "札幌記念を分析してください",
        "有馬記念の予想をお願いします",
        "2025年の日本ダービーを分析して",
        "天皇賞秋のレース分析",
        "今週の宝塚記念を予想してください",
        "昨日の安田記念どうだった？",  # 辞書にあるレース
        "グランプリレースを分析して",  # 辞書にないレース
    ]
    
    print("=== レースアナリシスチャットハンドラーのテスト ===\n")
    
    for message in test_messages:
        print(f"テストメッセージ: '{message}'")
        
        # レースアナリシス要求かチェック
        is_race_request = race_analysis_chat_handler.is_race_analysis_request(message)
        print(f"レースアナリシス要求: {is_race_request}")
        
        if is_race_request:
            # レース情報の抽出
            race_info = race_analysis_chat_handler.extract_race_info(message)
            if race_info:
                print(f"抽出されたレース情報:")
                print(f"  - レース名: {race_info.get('race_name')}")
                print(f"  - 開催場: {race_info.get('venue')}")
                print(f"  - 距離: {race_info.get('distance')}")
                print(f"  - グレード: {race_info.get('grade')}")
                print(f"  - 日付: {race_info.get('race_date')}")
            else:
                print("レース情報が抽出できませんでした")
            
            # レースアナリシスリクエストの処理
            result = race_analysis_chat_handler.process_race_analysis_request(message)
            print(f"処理結果タイプ: {result.get('type')}")
            print(f"メッセージ（最初の200文字）: {result.get('message', '')[:200]}...")
        
        print("-" * 60 + "\n")
    
    # アーカイブからのデータ取得テスト
    print("=== アーカイブデータ取得テスト ===\n")
    
    # テスト用のレースデータ（実際のアーカイブページの形式）
    test_race_data = {
        'venue': '札幌',
        'race_number': 11,
        'race_name': '札幌記念（G2）',
        'distance': '2000m',
        'grade': 'G2',
        'horses': ['ドウデュース', 'プログノーシス', 'ジャスティンパレス', 'ダノンベルーガ'],
        'jockeys': ['武豊', 'C.ルメール', '横山和生', '戸崎圭太'],
        'posts': [1, 2, 3, 4],
        'horse_numbers': [1, 2, 3, 4],
        'track_condition': '良'
    }
    
    # レース分析エンジンのテスト
    from services.race_analysis_engine import race_analysis_engine
    
    print("レース分析エンジンでテストデータを分析中...")
    analysis_result = race_analysis_engine.analyze_race(test_race_data)
    
    if 'error' in analysis_result:
        print(f"エラー: {analysis_result['error']}")
    else:
        print(f"分析成功!")
        print(f"レース情報: {analysis_result.get('race_info', {}).get('race_name')}")
        print(f"分析結果数: {len(analysis_result.get('results', []))}")
        
        # 上位3頭を表示
        results = analysis_result.get('results', [])
        if results:
            print("\n上位3頭:")
            for i, result in enumerate(results[:3]):
                print(f"{i+1}位: {result['horse']} × {result['jockey']} - {result['total_score']:.1f}点")
                print(f"     馬: {result['horse_score']:.1f}点, 騎手: {result['jockey_score']:.1f}点")
    
    # フォーマットされた応答のテスト
    print("\n=== フォーマット済み応答 ===\n")
    formatted_response = race_analysis_chat_handler.format_analysis_response(analysis_result)
    print(formatted_response[:1000] + "...")  # 最初の1000文字のみ表示

if __name__ == "__main__":
    asyncio.run(test_race_analysis())