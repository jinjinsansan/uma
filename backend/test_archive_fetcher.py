"""
アーカイブフェッチャーのテスト
"""
import asyncio
from services.archive_race_fetcher import archive_fetcher

async def test_archive_fetcher():
    """アーカイブフェッチャーのテスト"""
    
    print("=== アーカイブフェッチャーのテスト ===\n")
    
    # 1. 特定の日付・開催場・レース番号でデータ取得
    print("1. 札幌記念（2025-08-18 札幌11R）のデータ取得テスト")
    race_data = archive_fetcher.get_race_data("2025-08-18", "札幌", 11)
    
    if race_data:
        print(f"✅ レースデータ取得成功!")
        print(f"   - レース名: {race_data.get('race_name')}")
        print(f"   - 開催場: {race_data.get('venue')}")
        print(f"   - 距離: {race_data.get('distance')}")
        print(f"   - グレード: {race_data.get('grade')}")
        print(f"   - 出走頭数: {len(race_data.get('horses', []))}")
        print(f"   - 馬名: {', '.join(race_data.get('horses', [])[:5])}...")
        print(f"   - 騎手: {', '.join(race_data.get('jockeys', [])[:5])}...")
    else:
        print("❌ レースデータ取得失敗")
    
    print("\n" + "-" * 60 + "\n")
    
    # 2. レース名での検索
    print("2. レース名での検索テスト（'札幌記念'）")
    matching_races = archive_fetcher.search_race_by_name("札幌記念", "2025-08-18")
    
    if matching_races:
        print(f"✅ {len(matching_races)}件のレースが見つかりました")
        for race in matching_races:
            print(f"   - {race.get('venue')} {race.get('race_number')}R: {race.get('race_name')}")
    else:
        print("❌ レースが見つかりませんでした")
    
    print("\n" + "-" * 60 + "\n")
    
    # 3. 関屋記念の検索
    print("3. 関屋記念（G3）の検索テスト")
    matching_races = archive_fetcher.search_race_by_name("関屋記念", "2025-08-18")
    
    if matching_races:
        print(f"✅ {len(matching_races)}件のレースが見つかりました")
        for race in matching_races:
            print(f"   - {race.get('venue')} {race.get('race_number')}R: {race.get('race_name')}")
            print(f"     出走馬: {len(race.get('horses', []))}頭")
    else:
        print("❌ レースが見つかりませんでした")
    
    print("\n" + "-" * 60 + "\n")
    
    # 4. 存在しない日付のテスト
    print("4. 存在しない日付のテスト（2025-08-19）")
    race_data = archive_fetcher.get_race_data("2025-08-19", "東京", 11)
    
    if race_data:
        print("⚠️ データが見つかりました（想定外）")
    else:
        print("✅ 正しくNoneが返されました")
    
    print("\n" + "-" * 60 + "\n")
    
    # 5. キャッシュのテスト
    print("5. キャッシュ機能のテスト")
    import time
    
    start_time = time.time()
    race_data1 = archive_fetcher.get_race_data("2025-08-18", "札幌", 11)
    first_call_time = time.time() - start_time
    
    start_time = time.time()
    race_data2 = archive_fetcher.get_race_data("2025-08-18", "札幌", 11)
    second_call_time = time.time() - start_time
    
    print(f"   - 初回呼び出し: {first_call_time:.4f}秒")
    print(f"   - 2回目呼び出し（キャッシュ）: {second_call_time:.4f}秒")
    print(f"   - 高速化率: {first_call_time / second_call_time:.1f}倍")

if __name__ == "__main__":
    asyncio.run(test_archive_fetcher())