#!/usr/bin/env python3
"""
CDNファイル内の問題データを特定
"""

import json
import requests

def find_problem_data_in_cdn():
    """CDNファイル内の問題データを特定"""
    
    print("=== CDNファイル内問題データ特定 ===\n")
    
    cdn_url = "https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/jockey_knowledge.json"
    
    try:
        print("CDNファイル取得中...")
        response = requests.get(cdn_url, timeout=60)
        response.raise_for_status()
        
        cdn_data = response.json()
        print(f"CDNファイル読み込み完了: {len(cdn_data)}騎手")
        
        # 問題データを検索
        problem_count = 0
        problem_examples = []
        
        for jockey_name, jockey_data in cdn_data.items():
            post_stats = jockey_data.get('post_position_stats', {})
            
            if not isinstance(post_stats, dict):
                problem_count += 1
                problem_examples.append({
                    'jockey': jockey_name,
                    'issue': f'post_position_stats が辞書でない: {type(post_stats)}',
                    'value': str(post_stats)[:100]
                })
                continue
            
            for waku_str, stats in post_stats.items():
                if not isinstance(stats, dict):
                    problem_count += 1
                    problem_examples.append({
                        'jockey': jockey_name,
                        'waku': waku_str,
                        'issue': f'statsが辞書でない: {type(stats)}',
                        'value': str(stats)[:100]
                    })
                    
                    if len(problem_examples) >= 10:  # 最初の10件で十分
                        break
            
            if len(problem_examples) >= 10:
                break
        
        print(f"\n=== 問題データ発見結果 ===")
        print(f"総問題数: {problem_count}件")
        
        if problem_examples:
            print(f"\n問題例（最初の{len(problem_examples)}件）:")
            for i, problem in enumerate(problem_examples, 1):
                print(f"{i}. 騎手: {problem['jockey']}")
                if 'waku' in problem:
                    print(f"   枠: {problem['waku']}")
                print(f"   問題: {problem['issue']}")
                print(f"   値: {problem['value']}")
                print()
                
            # 問題データを詳細保存
            with open('/tmp/cdn_problem_data.json', 'w', encoding='utf-8') as f:
                json.dump(problem_examples, f, ensure_ascii=False, indent=2)
            print(f"詳細データを /tmp/cdn_problem_data.json に保存")
            
            # 特定の問題騎手で実際のエラーを再現
            print(f"\n=== エラー再現テスト ===")
            problem_jockey = problem_examples[0]['jockey']
            print(f"問題騎手 '{problem_jockey}' でエラー再現:")
            
            try:
                # 問題のあるget_jockey_post_position_fukusho_ratesを実行
                from services.jockey_knowledge_manager import JockeyKnowledgeManager
                
                # 一時的にCDNデータを使用してテスト
                manager = JockeyKnowledgeManager()
                manager.jockey_data = cdn_data  # CDNデータを直接設定
                
                result = manager.get_jockey_post_position_fukusho_rates([problem_jockey])
                print("   ✅ エラーなし（修正コードが有効）")
                
            except Exception as e:
                print(f"   ❌ エラー再現成功: {e}")
                
        else:
            print("✅ CDNファイルに問題データは見つかりませんでした")
            print("別の原因を調査する必要があります")
        
    except Exception as e:
        print(f"CDNファイル調査エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    find_problem_data_in_cdn()