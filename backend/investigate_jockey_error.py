#!/usr/bin/env python3
"""
'int' object has no attribute 'get' エラーの完全調査
jockey_knowledge.jsonファイルのデータ構造を完全に分析
"""

import json
import os
from typing import Dict, Any

def investigate_jockey_data():
    """騎手データの詳細構造を調査"""
    
    # ファイルパス
    file_path = "/tmp/jockey_knowledge_cache.json"  # キャッシュファイル
    fallback_path = os.path.join(os.path.dirname(__file__), '../data/jockey_knowledge.json')
    
    data = None
    used_path = None
    
    # キャッシュファイルまたはローカルファイルを読み込み
    for path in [file_path, fallback_path]:
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                used_path = path
                print(f"✅ ファイル読み込み成功: {path}")
                break
            except Exception as e:
                print(f"❌ ファイル読み込みエラー ({path}): {e}")
                continue
    
    if not data:
        print("❌ 騎手データファイルが見つかりません")
        return
    
    print(f"📊 総騎手数: {len(data)}名")
    print(f"📁 使用ファイル: {used_path}")
    
    # 1. データ構造の基本分析
    print("\n=== 1. データ構造基本分析 ===")
    sample_jockey = next(iter(data.keys()))
    sample_data = data[sample_jockey]
    print(f"サンプル騎手: '{sample_jockey}'")
    print(f"データキー: {list(sample_data.keys())}")
    
    # 2. post_position_statsの詳細分析
    print("\n=== 2. post_position_stats詳細分析 ===")
    post_stats = sample_data.get('post_position_stats', {})
    print(f"枠順データ型: {type(post_stats)}")
    print(f"枠数: {len(post_stats)}")
    
    # 3つの騎手の枠順データをサンプル分析
    test_jockeys = list(data.keys())[:3]
    
    for jockey_name in test_jockeys:
        print(f"\n--- {jockey_name} ---")
        jockey_data = data[jockey_name]
        post_stats = jockey_data.get('post_position_stats', {})
        
        if not post_stats:
            print("  枠順データなし")
            continue
            
        print(f"  枠順データ型: {type(post_stats)}")
        
        # 各枠のデータを詳細分析
        problem_found = False
        for waku_str, stats in post_stats.items():
            stats_type = type(stats)
            print(f"  {waku_str}: {stats_type} = {stats}")
            
            # 問題の特定: statsが辞書でない場合
            if not isinstance(stats, dict):
                print(f"  ⚠️ 問題発見: {waku_str}のstatsが辞書でない({stats_type})")
                problem_found = True
            elif 'race_count' not in stats or 'fukusho_rate' not in stats:
                print(f"  ⚠️ 問題発見: {waku_str}に必要キーがない: {stats.keys()}")
                problem_found = True
            else:
                race_count_type = type(stats.get('race_count'))
                fukusho_rate_type = type(stats.get('fukusho_rate'))
                print(f"    race_count: {race_count_type} = {stats.get('race_count')}")
                print(f"    fukusho_rate: {fukusho_rate_type} = {stats.get('fukusho_rate')}")
        
        if not problem_found:
            print("  ✅ この騎手のデータは正常")
    
    # 3. エラーの再現
    print("\n=== 3. エラー再現テスト ===")
    error_count = 0
    total_waku_count = 0
    
    for jockey_name, jockey_data in list(data.items())[:10]:  # 最初の10名をテスト
        post_stats = jockey_data.get('post_position_stats', {})
        if not post_stats or not isinstance(post_stats, dict):
            continue
            
        for waku_str, stats in post_stats.items():
            total_waku_count += 1
            try:
                # エラーの原因となるコードを実行
                if not isinstance(stats, dict):
                    print(f"❌ エラー発見: {jockey_name}の{waku_str} - statsが{type(stats)}: {stats}")
                    error_count += 1
                else:
                    race_count = stats.get('race_count', 0)
                    fukusho_rate = stats.get('fukusho_rate', 0)
            except Exception as e:
                print(f"❌ エラー発生: {jockey_name}の{waku_str} - {e}")
                print(f"   statsの型: {type(stats)}, 値: {stats}")
                error_count += 1
    
    print(f"\n📊 エラー統計:")
    print(f"  総枠数: {total_waku_count}")
    print(f"  エラー数: {error_count}")
    print(f"  エラー率: {error_count/total_waku_count*100:.2f}%" if total_waku_count > 0 else "  エラー率: N/A")
    
    # 4. 特定の騎手での詳細調査（新潟4R騎手）
    print("\n=== 4. 新潟4R騎手での詳細調査 ===")
    niigata_4r_jockeys = [
        '菅原隆一', '水沼元輝', '津村明秀', '団野大成', '岩部純二',
        '吉田豊　', '石田拓郎', '木幡巧也', '菅原明良', '原優介',
        '木幡初也', '上里太陽', '佐藤翔馬', '武藤雅', '遠藤健太'
    ]
    
    for jockey_name in niigata_4r_jockeys:
        if jockey_name in data:
            print(f"\n--- {jockey_name} ---")
            jockey_data = data[jockey_name]
            post_stats = jockey_data.get('post_position_stats', {})
            
            if not post_stats:
                print("  枠順データなし")
                continue
                
            # エラーの原因となる枠をチェック
            error_waku = []
            for waku_str, stats in post_stats.items():
                if not isinstance(stats, dict):
                    error_waku.append(f"{waku_str}({type(stats)})")
            
            if error_waku:
                print(f"  ❌ 問題枠: {', '.join(error_waku)}")
            else:
                print("  ✅ 全枠正常")
    
    return error_count > 0

if __name__ == "__main__":
    has_error = investigate_jockey_data()
    if has_error:
        print("\n🚨 データファイルに問題が発見されました！")
    else:
        print("\n✅ データファイルは正常です")