#!/usr/bin/env python3
"""
ViewLogicエンジンを直接インポートして、実際のレースデータでテスト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.viewlogic_engine import ViewLogicEngine

def test_direct_viewlogic():
    """実際のレースシナリオでViewLogicをテスト"""
    
    print("ViewLogicエンジンを初期化中...")
    engine = ViewLogicEngine()
    
    # 新潟4Rのようなレースデータ（フロントエンドから送られてくるデータと同じ形式）
    race_data = {
        'venue': '新潟',
        'distance': 1200,
        'track_type': '芝',
        'horses': [
            'イージーブリージー', 'エストゥペンダ', 'ウンエン',
            'アランチャータ', 'ロジアラサン', 'ピッチホルン'
        ],
        'jockeys': [
            '武豊', '川田', 'ルメール',
            '戸崎', '松山', '福永'
        ],
        'posts': [1, 2, 3, 4, 5, 6]
    }
    
    print(f"テストレース: {race_data['venue']}{race_data['distance']}m{race_data['track_type']}")
    print(f"騎手: {race_data['jockeys']}")
    
    try:
        # 傾向分析を実行
        print("\n傾向分析を実行中...")
        result = engine.analyze_course_trend(race_data)
        
        if result.get('status') == 'success':
            print("\n✅ 傾向分析成功！")
            
            # 騎手の枠順別成績を確認
            jockey_post_stats = result.get('trends', {}).get('jockey_post_performance', {})
            print(f"\n騎手の枠順別成績:")
            for jockey, stats in list(jockey_post_stats.items())[:3]:  # 最初の3騎手のみ表示
                print(f"\n{jockey}:")
                if isinstance(stats, dict):
                    for key, value in stats.items():
                        if key == 'all_post_stats' and isinstance(value, dict):
                            print(f"  枠順別複勝率:")
                            for category, cat_stats in value.items():
                                if isinstance(cat_stats, dict):
                                    rate = cat_stats.get('fukusho_rate', 0)
                                    count = cat_stats.get('race_count', 0)
                                    print(f"    {category}: {rate:.1f}% ({count}レース)")
                        elif key == 'assigned_post':
                            print(f"  割り当て枠: {value}")
            
            # エラーチェック
            error_messages = [
                "'int' object has no attribute 'get'",
                "エラーが発生しました",
                "ViewLogic分析中にエラー"
            ]
            
            insights = result.get('insights', '')
            for error_msg in error_messages:
                if error_msg in str(insights):
                    print(f"\n❌ エラーメッセージが含まれています: {error_msg}")
                    return False
            
            print("\n✅ エラーメッセージは含まれていません")
            return True
        else:
            print(f"\n❌ 傾向分析失敗: {result}")
            return False
            
    except Exception as e:
        print(f"\n❌ エラー発生: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_direct_viewlogic()
    if success:
        print("\n✅ ViewLogic修正は正常に動作しています！")
        print("これでデプロイ可能です。")
    else:
        print("\n❌ まだ問題が残っています")