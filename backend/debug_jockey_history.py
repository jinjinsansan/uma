#!/usr/bin/env python3
"""
騎手履歴取得メソッドのデバッグ
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.viewlogic_engine import ViewLogicEngine

def debug_jockey_history():
    """騎手履歴取得メソッドを詳細デバッグ"""
    
    print("🔍 騎手履歴取得メソッド詳細デバッグ")
    print("=" * 50)
    
    # ViewLogicエンジン初期化
    try:
        engine = ViewLogicEngine()
        print("✅ ViewLogicエンジン初期化完了")
    except Exception as e:
        print(f"❌ ViewLogicエンジン初期化エラー: {e}")
        return
    
    # テスト騎手名
    test_jockeys = ['川田将雅', '武豊', 'C.ルメール']
    
    for jockey_name in test_jockeys:
        print(f"\n【{jockey_name}のテスト】")
        print("-" * 30)
        
        # Step 1: 正規化テスト
        normalized = engine._normalize_jockey_name(jockey_name)
        print(f"1. 正規化: 「{jockey_name}」 → 「{normalized}」")
        
        # Step 2: 騎手マネージャーの状態確認
        if engine.jockey_manager.is_loaded():
            print("2. 騎手マネージャー: ✅ 読み込み済み")
        else:
            print("2. 騎手マネージャー: ❌ 未読み込み")
            continue
            
        # Step 3: 直接データ取得テスト
        direct_data = engine.jockey_manager.get_jockey_data(normalized)
        if direct_data:
            print("3. 直接データ取得: ✅ 成功")
            print(f"   データキー: {list(direct_data.keys())[:5]}...")
        else:
            print("3. 直接データ取得: ❌ 失敗")
            continue
        
        # Step 4: get_jockey_historyメソッドテスト
        try:
            result = engine.get_jockey_history(jockey_name)
            print("4. get_jockey_history実行: ✅ 成功")
            print(f"   ステータス: {result.get('status')}")
            print(f"   メッセージ: {result.get('message', '')}")
            
            if result['status'] == 'success':
                stats = result.get('stats', {})
                print(f"   統計データキー: {list(stats.keys())}")
                
                # 各統計の詳細
                if 'venue_course_stats' in stats:
                    venue_count = len(stats['venue_course_stats'])
                    print(f"   競馬場・距離別: {venue_count}件")
                
                if 'overall_stats' in stats:
                    overall = stats['overall_stats']
                    total_races = overall.get('total_races_analyzed', 0)
                    print(f"   総分析レース: {total_races}戦")
            
        except Exception as e:
            print(f"4. get_jockey_history実行: ❌ エラー - {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("🏁 デバッグ完了")

if __name__ == "__main__":
    debug_jockey_history()