#!/usr/bin/env python3
"""
ViewLogicエラーの完全な根本原因調査
全ての可能性を排除して真の原因を特定
"""

import json
import os
import traceback
from typing import Dict, Any

def investigate_all_possible_causes():
    """全ての可能な原因を調査"""
    
    print("=== ViewLogicエラー 完全調査 ===\n")
    
    # 1. CDNからダウンロードされたファイルを調査
    print("1. CDNからダウンロードされた騎手ナレッジファイルを調査")
    
    try:
        from services.jockey_knowledge_manager import JockeyKnowledgeManager
        
        # マネージャーを初期化（CDNからダウンロード）
        manager = JockeyKnowledgeManager()
        
        print(f"   総騎手数: {len(manager.jockey_data)}")
        print(f"   データロード状況: {manager.is_loaded()}")
        
        # 実際に問題のあるデータを探す
        problem_jockeys = []
        problem_data = []
        
        for jockey_name, jockey_data in manager.jockey_data.items():
            post_stats = jockey_data.get('post_position_stats', {})
            if not isinstance(post_stats, dict):
                problem_jockeys.append((jockey_name, f"post_position_stats が辞書でない: {type(post_stats)}"))
                continue
                
            for waku_str, stats in post_stats.items():
                if not isinstance(stats, dict):
                    problem_jockeys.append((jockey_name, f"{waku_str}: statsが辞書でない: {type(stats)} = {stats}"))
                    problem_data.append({
                        'jockey': jockey_name,
                        'waku': waku_str,
                        'stats_type': str(type(stats)),
                        'stats_value': str(stats)
                    })
        
        if problem_jockeys:
            print(f"\n   🚨 問題データ発見: {len(problem_jockeys)}件")
            for jockey, issue in problem_jockeys[:5]:  # 最初の5件を表示
                print(f"      {jockey}: {issue}")
            
            # 詳細データを保存
            with open('/tmp/viewlogic_problem_data.json', 'w', encoding='utf-8') as f:
                json.dump(problem_data, f, ensure_ascii=False, indent=2)
            print(f"   詳細データを /tmp/viewlogic_problem_data.json に保存")
        else:
            print("   ✅ 全騎手のデータが正常です")
        
    except Exception as e:
        print(f"   ❌ CDNファイル調査でエラー: {e}")
        traceback.print_exc()
    
    # 2. ViewLogicエンジンでの実際のエラー再現
    print("\n2. ViewLogicエンジンでの実際のエラー再現")
    
    try:
        from services.viewlogic_engine import ViewLogicEngine
        
        # 実際のレースデータでテスト（新潟4R）
        race_data = {
            'venue': '新潟',
            'distance': 1200,
            'track_type': '芝',
            'horses': [
                'ベネスティローザ', 'ジュリスタ', 'アンヘルカイド', 'ミラコレジェンヌ', 'エテオクロス',
                'ピンパンポン', 'ピコチマチ', 'シンフォニーシーズ', 'マオノクラッシュ', 'キタノライブリー',
                'ビアルベーロ', 'セイウンヤタガラス', 'ブライトビギニング', 'アオイハナミチ', 'ロドラント'
            ],
            'jockeys': [
                '菅原隆一', '水沼元輝', '津村明秀', '団野大成', '岩部純二',
                '吉田豊', '石田拓郎', '木幡巧也', '菅原明良', '原優介',
                '木幡初也', '上里太陽', '佐藤翔馬', '武藤雅', '遠藤健太'
            ],
            'posts': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
        }
        
        print(f"   テストレース: {race_data['venue']} {race_data['distance']}m {race_data['track_type']}")
        print(f"   騎手数: {len(race_data['jockeys'])}")
        
        engine = ViewLogicEngine()
        
        # ViewLogic傾向分析を実行
        result = engine.analyze_course_trend(race_data)
        print("   ✅ ViewLogic傾向分析が正常完了")
        
    except Exception as e:
        print(f"   ❌ ViewLogicエンジンでエラー発生: {e}")
        print(f"   エラータイプ: {type(e).__name__}")
        traceback.print_exc()
        
        # スタックトレースから正確なエラー発生場所を特定
        tb = traceback.format_exc()
        lines = tb.split('\n')
        for i, line in enumerate(lines):
            if "'int' object has no attribute 'get'" in line:
                print(f"\n   🎯 エラー発生場所特定:")
                print(f"      {lines[i-2] if i-2 >= 0 else ''}")
                print(f"      {lines[i-1] if i-1 >= 0 else ''}")
                print(f"   -> {line}")
                break
    
    # 3. 直接的なjockey_knowledge_manager.pyのテスト
    print("\n3. 騎手ナレッジマネージャーの直接テスト")
    
    try:
        from services.jockey_knowledge_manager import JockeyKnowledgeManager
        
        manager = JockeyKnowledgeManager()
        
        # 新潟4Rの騎手で直接テスト
        test_jockeys = [
            '菅原隆一', '水沼元輝', '津村明秀', '団野大成', '岩部純二',
            '吉田豊', '石田拓郎', '木幡巧也', '菅原明良', '原優介',
            '木幡初也', '上里太陽', '佐藤翔馬', '武藤雅', '遠藤健太'
        ]
        
        print(f"   テスト騎手: {len(test_jockeys)}名")
        
        # get_jockey_post_position_fukusho_rates を直接呼び出し
        result = manager.get_jockey_post_position_fukusho_rates(test_jockeys)
        print(f"   ✅ get_jockey_post_position_fukusho_rates 正常完了")
        print(f"   結果: {len(result)}名分のデータ取得")
        
    except Exception as e:
        print(f"   ❌ 騎手ナレッジマネージャーでエラー発生: {e}")
        print(f"   エラータイプ: {type(e).__name__}")
        traceback.print_exc()
    
    # 4. メモリ内データの詳細調査
    print("\n4. メモリ内データの詳細調査")
    
    try:
        from services.jockey_knowledge_manager import JockeyKnowledgeManager
        
        manager = JockeyKnowledgeManager()
        
        # 特定の騎手のデータを詳細調査
        test_jockey = '武豊'
        full_name_patterns = [
            '武豊',
            '武豊　',
            '武豊　　',
            '武　豊',
            '武　豊　'
        ]
        
        found_name = None
        for pattern in full_name_patterns:
            if pattern in manager.jockey_data:
                found_name = pattern
                break
        
        if found_name:
            print(f"   武豊発見: '{found_name}' (長さ: {len(found_name)})")
            jockey_data = manager.jockey_data[found_name]
            post_stats = jockey_data.get('post_position_stats', {})
            
            print(f"   post_position_stats型: {type(post_stats)}")
            print(f"   枠数: {len(post_stats)}")
            
            # 各枠のstatsを詳細チェック
            for waku_str, stats in post_stats.items():
                stats_type = type(stats)
                print(f"      {waku_str}: {stats_type}")
                
                if not isinstance(stats, dict):
                    print(f"         🚨 問題発見: statsが{stats_type} = {stats}")
                else:
                    race_count = stats.get('race_count', 'なし')
                    fukusho_rate = stats.get('fukusho_rate', 'なし')
                    print(f"         race_count: {race_count}, fukusho_rate: {fukusho_rate}")
        else:
            print("   武豊が見つかりません")
            # 武を含む騎手を検索
            takeshi_jockeys = [name for name in manager.jockey_data.keys() if '武' in name]
            print(f"   '武'を含む騎手: {takeshi_jockeys[:5]}")
        
    except Exception as e:
        print(f"   ❌ メモリ内データ調査でエラー: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    investigate_all_possible_causes()
    print("\n=== 完全調査終了 ===")