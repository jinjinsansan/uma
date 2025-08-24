#!/usr/bin/env python3
"""
IMLogicで全馬表示のテスト
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.imlogic_engine import IMLogicEngine

def test_all_horses_display():
    """全馬表示（データなし含む）のテスト"""
    print("=== IMLogic 全馬表示テスト ===\n")
    
    engine = IMLogicEngine()
    
    # 新潟2Rのデータ（ネポティズムベビー含む）
    race_data = {
        'venue': '新潟',
        'race_number': 2,
        'race_name': '3歳未勝利',
        'distance': '1200m',
        'track_condition': '良',
        'horses': [
            'ネポティズムベビー',
            'メリザンド',
            'ミルキープリンセス',
            'ザタイムズ',
            'ヴィーナスゼファー',
            'セラドピラール',
            'アイスリーディング',
            'アルマリカシバ',
            'センジュコスモス',
            'グランカッサ',
            'ルージュメアート',
            'ハクシンマルペンサ',
            'ピンキースウェア',
            'ライヴスプーン'
        ],
        'jockeys': [
            '津村明秀', '岩田望来', '原優介', '大野拓弥',
            '斎藤新', '丸山元気', '石田拓郎', '上里直汰',
            '内田博幸', '今村聖奈', '岩田康誠', '佐藤翔馬',
            '石神深道', '遠藤汰月'
        ],
        'posts': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14],
        'horse_numbers': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
    }
    
    # バランス型
    balanced_weights = {
        '1_distance_aptitude': 8.3,
        '2_bloodline_evaluation': 8.3,
        '3_jockey_compatibility': 8.3,
        '4_trainer_evaluation': 8.3,
        '5_track_aptitude': 8.3,
        '6_weather_aptitude': 8.3,
        '7_popularity_factor': 8.3,
        '8_weight_impact': 8.3,
        '9_horse_weight_impact': 8.3,
        '10_corner_specialist': 8.4,
        '11_margin_analysis': 8.4,
        '12_time_index': 8.4
    }
    
    try:
        result = engine.analyze_race(race_data, 70, 30, balanced_weights)
        
        print(f"分析対象: {len(race_data['horses'])}頭")
        print(f"結果に含まれる馬: {len(result['results'])}頭")
        
        print("\n=== 上位5頭 ===")
        for r in result['results'][:5]:
            if r.get('data_status') == 'no_data':
                print(f"- {r['horse']} × {r['jockey']} [データなし]")
            else:
                print(f"{r['rank']}位: {r['horse']} × {r['jockey']} - 総合{r['total_score']:.2f}点")
        
        print("\n=== 全結果 ===")
        print("順位 | 馬名 | 騎手 | 総合スコア | 状態")
        print("-" * 60)
        for r in result['results']:
            if r.get('data_status') == 'no_data':
                print(f"  -  | {r['horse']:12} | {r['jockey']:8} | データなし")
            else:
                print(f" {r['rank']:2}  | {r['horse']:12} | {r['jockey']:8} | {r['total_score']:6.2f}点")
            
    except Exception as e:
        print(f"エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_all_horses_display()