"""
IMLogicエンジンのテスト
実際のユーザーシナリオを想定したテストケース
"""
import asyncio
import json
from datetime import datetime
from services.imlogic_engine import IMLogicEngine

# テスト用レースデータ（2024年有馬記念を想定）
TEST_RACE_DATA = {
    "venue": "中山",
    "race_number": 11,
    "race_name": "有馬記念（G1）",
    "distance": "2500m",
    "track_condition": "良",
    "horses": [
        "ドウデュース",
        "スターズオンアース",
        "ジャスティンパレス",
        "ローシャムパーク",
        "プログノーシス",
        "シャフリヤール",
        "ボッケリーニ",
        "ノースブリッジ"
    ],
    "jockeys": [
        "武豊",
        "C.ルメール",
        "横山和生",
        "菱田裕二",
        "岩田望来",
        "川田将雅",
        "松山弘平",
        "戸崎圭太"
    ],
    "posts": [1, 2, 3, 4, 5, 6, 7, 8],
    "horse_numbers": [1, 2, 3, 4, 5, 6, 7, 8]
}

# テストケース1: 標準的なユーザー（ILogicデフォルトに近い）
TEST_CASE_1 = {
    "name": "標準ユーザー",
    "description": "ILogicのデフォルト設定とほぼ同じ",
    "horse_weight": 70,
    "jockey_weight": 30,
    "item_weights": {
        "1_distance_aptitude": 8.33,
        "2_bloodline_evaluation": 8.33,
        "3_jockey_compatibility": 8.33,
        "4_trainer_evaluation": 8.33,
        "5_track_aptitude": 8.33,
        "6_weather_aptitude": 8.33,
        "7_popularity_factor": 8.33,
        "8_weight_impact": 8.33,
        "9_horse_weight_impact": 8.33,
        "10_corner_specialist": 8.33,
        "11_margin_analysis": 8.33,
        "12_time_index": 8.37
    }
}

# テストケース2: 血統重視ユーザー
TEST_CASE_2 = {
    "name": "血統重視ユーザー",
    "description": "血統評価に40%の重みを置く",
    "horse_weight": 80,
    "jockey_weight": 20,
    "item_weights": {
        "1_distance_aptitude": 5.0,
        "2_bloodline_evaluation": 40.0,  # 血統に40%！
        "3_jockey_compatibility": 5.0,
        "4_trainer_evaluation": 5.0,
        "5_track_aptitude": 5.0,
        "6_weather_aptitude": 5.0,
        "7_popularity_factor": 5.0,
        "8_weight_impact": 5.0,
        "9_horse_weight_impact": 5.0,
        "10_corner_specialist": 5.0,
        "11_margin_analysis": 5.0,
        "12_time_index": 10.0
    }
}

# テストケース3: 騎手重視ユーザー
TEST_CASE_3 = {
    "name": "騎手重視ユーザー",
    "description": "騎手50%、騎手相性も重視",
    "horse_weight": 50,
    "jockey_weight": 50,
    "item_weights": {
        "1_distance_aptitude": 8.0,
        "2_bloodline_evaluation": 5.0,
        "3_jockey_compatibility": 25.0,  # 騎手相性重視
        "4_trainer_evaluation": 8.0,
        "5_track_aptitude": 8.0,
        "6_weather_aptitude": 5.0,
        "7_popularity_factor": 5.0,
        "8_weight_impact": 5.0,
        "9_horse_weight_impact": 5.0,
        "10_corner_specialist": 8.0,
        "11_margin_analysis": 8.0,
        "12_time_index": 10.0
    }
}

# テストケース4: タイム重視ユーザー
TEST_CASE_4 = {
    "name": "タイム重視ユーザー",
    "description": "タイムインデックスに50%の重み",
    "horse_weight": 90,
    "jockey_weight": 10,
    "item_weights": {
        "1_distance_aptitude": 10.0,
        "2_bloodline_evaluation": 5.0,
        "3_jockey_compatibility": 3.0,
        "4_trainer_evaluation": 3.0,
        "5_track_aptitude": 5.0,
        "6_weather_aptitude": 3.0,
        "7_popularity_factor": 3.0,
        "8_weight_impact": 3.0,
        "9_horse_weight_impact": 3.0,
        "10_corner_specialist": 5.0,
        "11_margin_analysis": 7.0,
        "12_time_index": 50.0  # タイムに50%！
    }
}

async def test_imlogic_case(engine: IMLogicEngine, test_case: dict):
    """個別のテストケースを実行"""
    print(f"\n{'='*80}")
    print(f"🧪 テストケース: {test_case['name']}")
    print(f"📝 説明: {test_case['description']}")
    print(f"⚖️  比率: 馬{test_case['horse_weight']}% / 騎手{test_case['jockey_weight']}%")
    print(f"{'='*80}")
    
    # IMLogic分析を実行
    result = await engine.analyze_race(
        race_data=TEST_RACE_DATA,
        horse_weight=test_case['horse_weight'],
        jockey_weight=test_case['jockey_weight'],
        item_weights=test_case['item_weights']
    )
    
    if 'error' in result:
        print(f"❌ エラー: {result['error']}")
        return
    
    # 結果を表示
    print(f"\n🏇 {result['race_info']['race_name']} の分析結果")
    print(f"📍 {result['race_info']['venue']} {result['race_info']['distance']}")
    print(f"🌤️  馬場: {result['race_info']['track_condition']}")
    
    print(f"\n📊 IMLogicランキング:")
    print(f"{'順位':<4} {'馬番':<4} {'馬名':<20} {'騎手':<15} {'総合':<8} {'馬':<8} {'騎手':<8}")
    print("-" * 80)
    
    for r in result['results'][:8]:  # 上位8頭のみ表示
        if 'error' not in r:
            print(f"{r['rank']:<4} {r['horse_number']:<4} {r['horse']:<20} {r['jockey']:<15} "
                  f"{r['total_score']:<8.1f} {r['horse_score']:<8.1f} {r['jockey_score']:<8.1f}")
    
    # サマリー情報
    if 'summary' in result:
        summary = result['summary']
        print(f"\n📈 分析サマリー:")
        print(f"  🥇 1位: {summary['top_horse']['name']} ({summary['top_horse']['score']}点)")
        print(f"  📊 スコア分布: 最高{summary['score_distribution']['highest']}点 "
              f"〜 最低{summary['score_distribution']['lowest']}点 "
              f"(平均{summary['score_distribution']['average']}点)")
        
        if summary['custom_weights_impact']:
            print(f"\n  💡 重み付けの影響（上位3項目）:")
            for impact in summary['custom_weights_impact']:
                print(f"    - {impact['item']}: 重み{impact['weight']}% → 貢献{impact['contribution']}点")
    
    # 詳細情報（1位の馬のみ）
    if result['results']:
        top_horse = result['results'][0]
        if 'custom_item_scores' in top_horse and top_horse['custom_item_scores']:
            print(f"\n🔍 1位の馬（{top_horse['horse']}）の詳細分析:")
            items = sorted(
                top_horse['custom_item_scores'].items(),
                key=lambda x: x[1]['contribution'],
                reverse=True
            )
            for item_name, item_data in items[:5]:  # 上位5項目
                print(f"  {item_name}: "
                      f"元スコア{item_data['original_score']}点 × "
                      f"重み{item_data['weight']}% = "
                      f"貢献{item_data['contribution']}点")

async def main():
    """メインテスト実行"""
    print("🚀 IMLogicエンジンテストを開始します")
    print(f"📅 実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # エンジンを初期化
        print("\n⚙️  IMLogicエンジンを初期化中...")
        engine = IMLogicEngine()
        print("✅ 初期化完了")
        
        # 各テストケースを実行
        test_cases = [TEST_CASE_1, TEST_CASE_2, TEST_CASE_3, TEST_CASE_4]
        
        for test_case in test_cases:
            await test_imlogic_case(engine, test_case)
            await asyncio.sleep(0.5)  # 少し待機
        
        # 結果の比較
        print(f"\n{'='*80}")
        print("📊 テストケース間の比較")
        print(f"{'='*80}")
        
        all_results = []
        for test_case in test_cases:
            result = await engine.analyze_race(
                race_data=TEST_RACE_DATA,
                horse_weight=test_case['horse_weight'],
                jockey_weight=test_case['jockey_weight'],
                item_weights=test_case['item_weights']
            )
            if 'results' in result and result['results']:
                all_results.append({
                    'name': test_case['name'],
                    'top3': [(r['horse'], r['total_score']) for r in result['results'][:3]]
                })
        
        # 各ケースの1位を比較
        print("\n🥇 各ケースの1位:")
        for res in all_results:
            if res['top3']:
                print(f"  {res['name']}: {res['top3'][0][0]} ({res['top3'][0][1]}点)")
        
        print("\n✅ テスト完了")
        
    except Exception as e:
        print(f"\n❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())