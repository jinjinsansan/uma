#!/usr/bin/env python3
"""
騎手ナレッジファイルのデータ構造を調査
"""

import json
import requests
from typing import Dict, Any

def check_jockey_data_structure():
    """騎手ナレッジファイルのデータ構造を確認"""
    
    print("騎手ナレッジファイルをダウンロード中...")
    url = 'https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/jockey_knowledge.json'
    
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        data = response.json()
        print(f"騎手データ数: {len(data)}")
        
        # 問題のあるデータを探す
        problematic_jockeys = []
        
        for jockey_name, jockey_data in list(data.items())[:50]:  # 最初の50騎手をチェック
            if isinstance(jockey_data, dict) and 'post_position_stats' in jockey_data:
                post_stats = jockey_data['post_position_stats']
                
                if isinstance(post_stats, dict):
                    for waku_str, stats in post_stats.items():
                        if not isinstance(stats, dict):
                            problematic_jockeys.append({
                                'jockey': jockey_name,
                                'waku': waku_str,
                                'type': type(stats).__name__,
                                'value': stats
                            })
                            print(f"問題発見: {jockey_name} の {waku_str} が {type(stats).__name__} 型: {stats}")
                else:
                    print(f"警告: {jockey_name} の post_position_stats が辞書ではない: {type(post_stats).__name__}")
        
        if problematic_jockeys:
            print(f"\n問題のあるデータが {len(problematic_jockeys)} 件見つかりました")
            for item in problematic_jockeys[:10]:  # 最初の10件を表示
                print(f"  騎手: {item['jockey']}, 枠: {item['waku']}, 型: {item['type']}, 値: {item['value']}")
        else:
            print("\n最初の50騎手には問題のあるデータは見つかりませんでした")
            
            # 正常なデータの例を表示
            for jockey_name, jockey_data in list(data.items())[:3]:
                if isinstance(jockey_data, dict) and 'post_position_stats' in jockey_data:
                    print(f"\n正常な例 - {jockey_name}:")
                    post_stats = jockey_data['post_position_stats']
                    if isinstance(post_stats, dict):
                        for waku_str, stats in list(post_stats.items())[:2]:
                            print(f"  {waku_str}: {stats}")
                    break
        
        return data
        
    except Exception as e:
        print(f"エラー: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    check_jockey_data_structure()