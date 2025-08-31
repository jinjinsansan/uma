#!/usr/bin/env python3
"""
複勝率表示修正の簡単なテスト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.viewlogic_engine import ViewLogicEngine

def test_percentage_fix():
    """複勝率表示修正の直接テスト"""
    
    print("🧪 複勝率表示修正テスト")
    print("=" * 50)
    
    engine = ViewLogicEngine()
    
    test_jockeys = ['川田将雅', '武豊']
    
    for jockey_name in test_jockeys:
        print(f"\n🧪 {jockey_name}騎手のデータテスト")
        
        try:
            result = engine.get_jockey_history(jockey_name)
            
            if result['status'] == 'success':
                print("   ✅ データ取得成功")
                
                # 統計データから複勝率をチェック
                statistics = result.get('statistics', {})
                overall_rate = statistics.get('総合複勝率', '')
                
                print(f"   総合複勝率: {overall_rate}")
                
                # recent_ridesの複勝率もチェック
                recent_rides = result.get('recent_rides', [])
                if recent_rides:
                    print("   個別成績:")
                    for i, ride in enumerate(recent_rides[:3]):  # 最初の3件のみ
                        venue = ride.get('競馬場', '')
                        distance = ride.get('距離', '')
                        rate = ride.get('複勝率', '')
                        print(f"     {venue}{distance}: 複勝率{rate}")
                
                # 異常な複勝率パターンをチェック
                abnormal_patterns = ['000.0%', '4000.0%', '500.0%', '1000.0%']
                content_str = str(result)
                has_abnormal = any(pattern in content_str for pattern in abnormal_patterns)
                
                if has_abnormal:
                    print("   ❌ 異常な複勝率表示検出")
                    for pattern in abnormal_patterns:
                        if pattern in content_str:
                            print(f"      → 検出: {pattern}")
                else:
                    print("   ✅ 複勝率表示は正常範囲内")
            else:
                print(f"   ❌ データ取得失敗: {result.get('message')}")
                
        except Exception as e:
            print(f"   ❌ エラー: {e}")
            # エラーが'int' object has no attribute 'get'かチェック
            if "'int' object has no attribute 'get'" in str(e):
                print("   💥 重要: 古いエラーパターンが再発生しました")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_percentage_fix()