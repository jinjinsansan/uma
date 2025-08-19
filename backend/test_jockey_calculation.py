#!/usr/bin/env python3
"""
騎手計算ロジックの詳細確認テスト
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.jockey_data_manager import jockey_manager
from services.jockey_name_mapper import normalize_jockey_name
import json

def test_jockey_calculation():
    """騎手計算の詳細を確認"""
    print("=== 騎手計算ロジック確認テスト ===\n")
    
    # テストケース
    test_cases = [
        {'jockey': '津村明秀', 'venue': '新潟', 'post': 2, 'sire': 'ディープインパクト'},
        {'jockey': '武豊', 'venue': '札幌', 'post': 1, 'sire': 'ディープインパクト'},
        {'jockey': 'C.ルメール', 'venue': '東京', 'post': 8, 'sire': 'キタサンブラック'},
        {'jockey': '川端', 'venue': '新潟', 'post': 1, 'sire': 'ロードカナロア'},
        {'jockey': '江田照', 'venue': '新潟', 'post': 3, 'sire': 'ハーツクライ'}
    ]
    
    for test in test_cases:
        print(f"\n{'='*60}")
        print(f"騎手: {test['jockey']}")
        print(f"開催場: {test['venue']}, 枠: {test['post']}, 父: {test['sire']}")
        print('-'*60)
        
        # 騎手名の正規化
        normalized_name = normalize_jockey_name(test['jockey'])
        print(f"正規化後の騎手名: {normalized_name}")
        
        # 騎手データの存在確認
        jockey_data = jockey_manager.get_jockey_data(normalized_name)
        if jockey_data:
            print(f"✅ 騎手データ: 存在する")
            
            # 各要素の計算
            venue_score = jockey_manager.calculate_venue_aptitude(normalized_name, test['venue'])
            post_score = jockey_manager.calculate_post_position_aptitude(normalized_name, test['post'])
            sire_score = jockey_manager.calculate_sire_aptitude(normalized_name, test['sire'])
            
            total_score = venue_score + post_score + sire_score
            
            print(f"\n【計算詳細】")
            print(f"開催場適性（{test['venue']}）: {venue_score:+.1f}点")
            
            # 開催場の詳細データを表示
            venue_stats = jockey_data.get('venue_course_stats', {})
            venue_races = 0
            venue_fukusho = 0
            for key, stats in venue_stats.items():
                if test['venue'] in key:
                    race_count = stats.get('race_count', 0)
                    fukusho_rate = stats.get('fukusho_rate', 0)
                    print(f"  - {key}: {race_count}戦, 複勝率{fukusho_rate}%")
                    venue_races += race_count
                    venue_fukusho += (fukusho_rate * race_count / 100)
            
            if venue_races > 0:
                overall_rate = venue_fukusho / venue_races
                print(f"  → 総合複勝率: {overall_rate:.1%}")
            
            print(f"\n枠順適性（枠{test['post']}）: {post_score:+.1f}点")
            post_data = jockey_data.get('post_position_stats', {}).get(f"枠{test['post']}", {})
            if post_data:
                print(f"  - {post_data.get('race_count', 0)}戦, 複勝率{post_data.get('fukusho_rate', 0)}%")
            
            print(f"\n種牡馬相性（{test['sire']}）: {sire_score:+.1f}点")
            sire_data = jockey_data.get('sire_stats', {}).get(test['sire'], {})
            if sire_data:
                print(f"  - {sire_data.get('total_races', 0)}戦, 複勝率{sire_data.get('fukusho_rate', 0)}%")
            
            print(f"\n【騎手総合スコア】: {total_score:+.1f}点")
            
            # 30%での影響を計算
            print(f"【最終的な貢献度】: {total_score * 0.3:+.1f}点（30%計算後）")
            
        else:
            print(f"❌ 騎手データ: 見つからない")
            print(f"【騎手総合スコア】: 0.0点（データなし）")
            print(f"【最終的な貢献度】: 0.0点（30%計算後）")

if __name__ == "__main__":
    test_jockey_calculation()