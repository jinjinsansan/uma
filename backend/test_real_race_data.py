#!/usr/bin/env python3
"""
実際のレースデータでViewLogicをテスト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.viewlogic_engine import ViewLogicEngine

def test_real_race():
    """実際のレースデータでテスト"""
    
    print("ViewLogicエンジンを初期化中...")
    engine = ViewLogicEngine()
    
    # 実際のレースデータ
    race_data = {
        'venue': '新潟',
        'distance': 1200,
        'track_type': 'ダート',  # ダートですね
        'horses': [
            'ナックエルドラド', 'メイショウコウベ', 'ナックシュバリエ',
            'サクラコーラル', 'フラッシュタイム', 'ニシノプライム',
            'グランダイト', 'ジュンビクトワール', 'ブラザービート',
            'アストラン', 'フェアゴー', 'ショージージョ',
            'メモリードライブ', 'ネバーランドリーム', 'ヴァルトバーデン'
        ],
        'jockeys': [
            '吉田豊', '大野', '木幡初',
            '丸山', '菊沢', '木幡巧',
            '上里', '荻野極', '内田博',
            '斎藤', '杉原', '武藤',
            '原', '遠藤', '江田照'
        ],
        'posts': [1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8]
    }
    
    print(f"テストレース: {race_data['venue']}{race_data['distance']}m{race_data['track_type']}")
    print(f"出走頭数: {len(race_data['horses'])}頭")
    print(f"騎手: {race_data['jockeys'][:5]}... (他{len(race_data['jockeys'])-5}名)")
    
    try:
        # 傾向分析を実行
        print("\n傾向分析を実行中...")
        result = engine.analyze_course_trend(race_data)
        
        if result.get('status') == 'success':
            print("\n✅ 傾向分析成功！")
            
            # 騎手の枠順別成績を確認（最初の5騎手）
            jockey_post_stats = result.get('trends', {}).get('jockey_post_performance', {})
            print(f"\n騎手の枠順別成績（上位5名）:")
            
            displayed = 0
            for jockey, stats in jockey_post_stats.items():
                if displayed >= 5:
                    break
                    
                print(f"\n{jockey}:")
                if isinstance(stats, dict):
                    assigned_post = stats.get('assigned_post', '不明')
                    post_category = stats.get('post_category', '不明')
                    print(f"  割り当て枠: {assigned_post} ({post_category})")
                    
                    # 枠順別成績
                    all_stats = stats.get('all_post_stats', {})
                    if isinstance(all_stats, dict):
                        for category, cat_stats in all_stats.items():
                            if isinstance(cat_stats, dict):
                                rate = cat_stats.get('fukusho_rate', 0)
                                count = cat_stats.get('race_count', 0)
                                if count > 0:  # データがある場合のみ表示
                                    print(f"    {category}: {rate:.1f}% ({count}レース)")
                else:
                    print(f"  データなし")
                
                displayed += 1
            
            # エラーチェック
            error_messages = [
                "'int' object has no attribute 'get'",
                "エラーが発生しました",
                "ViewLogic分析中にエラー"
            ]
            
            insights = str(result.get('insights', ''))
            for error_msg in error_messages:
                if error_msg in insights:
                    print(f"\n❌ エラーメッセージが含まれています: {error_msg}")
                    return False
            
            print("\n✅ エラーメッセージは含まれていません")
            
            # 傾向分析の洞察を表示（最初の500文字）
            print(f"\n分析洞察（一部）:")
            print(insights[:500] + "..." if len(insights) > 500 else insights)
            
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
    success = test_real_race()
    if success:
        print("\n" + "="*60)
        print("✅ ViewLogic修正は実際のレースデータで正常に動作しています！")
        print("これでデプロイ可能です。")
        print("="*60)
    else:
        print("\n❌ まだ問題が残っています")