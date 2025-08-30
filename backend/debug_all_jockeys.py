#!/usr/bin/env python3
"""
全騎手のデータ構造を徹底調査
"""

import json
import requests

def check_all_jockeys():
    """全騎手のデータを確認"""
    
    print("騎手ナレッジファイルをダウンロード中...")
    url = 'https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/jockey_knowledge.json'
    
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        data = response.json()
        print(f"騎手データ総数: {len(data)}")
        
        # 全騎手をチェック
        problematic_jockeys = []
        
        for jockey_name, jockey_data in data.items():
            if isinstance(jockey_data, dict) and 'post_position_stats' in jockey_data:
                post_stats = jockey_data['post_position_stats']
                
                if isinstance(post_stats, dict):
                    for waku_str, stats in post_stats.items():
                        if not isinstance(stats, dict):
                            problematic_jockeys.append({
                                'jockey': jockey_name,
                                'waku': waku_str,
                                'type': type(stats).__name__,
                                'value': str(stats)[:100]  # 最初の100文字のみ
                            })
                elif post_stats is not None:  # Noneでない場合のみ警告
                    problematic_jockeys.append({
                        'jockey': jockey_name,
                        'waku': 'post_position_stats',
                        'type': type(post_stats).__name__,
                        'value': str(post_stats)[:100]
                    })
        
        if problematic_jockeys:
            print(f"\n問題のあるデータが {len(problematic_jockeys)} 件見つかりました！")
            print("\n最初の20件:")
            for item in problematic_jockeys[:20]:
                print(f"  騎手: {item['jockey']:<10} 枠: {item['waku']:<20} 型: {item['type']:<10} 値: {item['value']}")
            
            # 問題の騎手名リストを作成
            problem_jockey_names = list(set([item['jockey'] for item in problematic_jockeys]))
            print(f"\n問題のある騎手名 ({len(problem_jockey_names)}名):")
            print(', '.join(problem_jockey_names[:20]))
        else:
            print("\nすべての騎手データは正常です！")
        
        # 特定の騎手（新潟4Rの騎手）のデータを確認
        check_jockeys = ['武豊', '川田', 'ルメール', '菅原隆一', '水沼元輝']
        print(f"\n特定騎手のデータ構造確認:")
        for jockey in check_jockeys:
            if jockey in data:
                print(f"\n{jockey}:")
                jockey_data = data[jockey]
                if 'post_position_stats' in jockey_data:
                    post_stats = jockey_data['post_position_stats']
                    print(f"  post_position_stats型: {type(post_stats).__name__}")
                    if isinstance(post_stats, dict):
                        print(f"  枠数: {len(post_stats)}")
                        for waku, stats in list(post_stats.items())[:2]:
                            print(f"    {waku}: {type(stats).__name__}")
                            if isinstance(stats, dict):
                                print(f"      keys: {list(stats.keys())}")
                else:
                    print(f"  post_position_statsなし")
            else:
                print(f"\n{jockey}: データなし")
        
    except Exception as e:
        print(f"エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_all_jockeys()