#!/usr/bin/env python3
"""
ViewLogicエンジンのテストスクリプト
3つの主要機能（展開予想、コース傾向、当日傾向）をテスト
"""

import sys
import os
import json
from datetime import datetime

# プロジェクトのルートディレクトリをPythonパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.viewlogic_engine import ViewLogicEngine


def print_section(title):
    """セクションタイトルを表示"""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)


def test_race_flow_prediction():
    """展開予想機能のテスト"""
    print_section("1. 展開予想機能のテスト")
    
    # テスト用レースデータ（実際の馬名を使用）
    race_data = {
        'venue': '東京',
        'race_number': 11,
        'race_name': '天皇賞（秋）',
        'distance': 2000,
        'horses': [
            'ドウデュース',
            'イクイノックス',
            'ジャスティンパレス',
            'ダノンベルーガ',
            'ノースブリッジ',
            'プログノーシス',
            'ガイアフォース',
            'エヒト',
            'サリエラ',
            'ローシャムパーク'
        ]
    }
    
    try:
        engine = ViewLogicEngine()
        result = engine.predict_race_flow(race_data)
        
        if result['status'] == 'success':
            print("✅ 展開予想成功")
            print(f"\n【レース情報】")
            print(f"  開催場: {result['race_info']['venue']}")
            print(f"  レース: {result['race_info']['race_number']}R - {result['race_info']['race_name']}")
            
            print(f"\n【ペース予測】")
            prediction = result['prediction']
            print(f"  予想ペース: {prediction['pace']} (確信度: {prediction['pace_confidence']}%)")
            
            print(f"\n【脚質分布】")
            for style_data in prediction['style_distribution']:
                print(f"  {style_data['style']}: {style_data['count']}頭")
                if style_data['horses']:
                    print(f"    馬: {', '.join(style_data['horses'])}")
            
            print(f"\n【有利な馬】")
            for horse in prediction['advantaged_horses']:
                print(f"  - {horse}")
            
            print(f"\n【不利な馬】")
            for horse in prediction['disadvantaged_horses']:
                print(f"  - {horse}")
            
            print(f"\n【分析頭数】 {result['analyzed_horses']}/{result['total_horses']}頭")
        else:
            print(f"❌ エラー: {result['message']}")
            
    except Exception as e:
        print(f"❌ 例外発生: {e}")
        import traceback
        traceback.print_exc()


def test_course_trend_analysis():
    """コース傾向分析のテスト"""
    print_section("2. コース傾向分析のテスト")
    
    try:
        engine = ViewLogicEngine()
        
        # 東京2000m芝のテスト
        result = engine.analyze_course_trend(
            venue='東京',
            distance=2000,
            track_type='芝'
        )
        
        if result['status'] == 'success':
            print("✅ コース傾向分析成功")
            print(f"\n【コース情報】")
            print(f"  {result['course_info']['venue']} {result['course_info']['distance']}m {result['course_info']['track_type'] or ''}")
            
            print(f"\n【騎手成績TOP5】")
            for i, jockey in enumerate(result['trends']['jockey_ranking'], 1):
                print(f"  {i}. {jockey['name']}: 勝率{jockey['win_rate']:.1%} 複勝率{jockey['fukusho_rate']:.1%}")
            
            print(f"\n【血統成績TOP3】")
            for i, sire in enumerate(result['trends']['sire_ranking'], 1):
                print(f"  {i}. {sire['name']}: 複勝率{sire['fukusho_rate']:.1%} ({sire['runs']}頭)")
            
            print(f"\n【枠順別成績】")
            for position, stats in result['trends']['post_position_stats'].items():
                print(f"  {position}: 勝率{stats['win_rate']:.1%} 複勝率{stats['fukusho_rate']:.1%}")
            
            print(f"\n【インサイト】")
            for insight in result['insights']:
                print(f"  • {insight}")
                
        else:
            print(f"❌ エラー: {result['message']}")
            
    except Exception as e:
        print(f"❌ 例外発生: {e}")
        import traceback
        traceback.print_exc()


def test_daily_trend_analysis():
    """当日傾向分析のテスト"""
    print_section("3. 当日傾向分析のテスト")
    
    try:
        engine = ViewLogicEngine()
        
        # 今日の日付でテスト
        today = datetime.now().strftime('%Y-%m-%d')
        result = engine.analyze_daily_trend(
            date=today,
            venue='東京'
        )
        
        if result['status'] == 'success':
            print("✅ 当日傾向分析成功")
            print(f"\n【開催情報】")
            print(f"  日付: {result['date']}")
            print(f"  開催場: {result['venue']}")
            print(f"  実施済みレース: {result['races_completed']}R")
            
            print(f"\n【脚質別成績】")
            for style, perf in result['trends']['running_style_performance'].items():
                print(f"  {style}: {perf['wins']}勝/{perf['runs']}頭 (勝率{perf['win_rate']:.1%})")
            
            print(f"\n【好調騎手TOP3】")
            for i, jockey in enumerate(result['trends']['hot_jockeys'], 1):
                print(f"  {i}. {jockey['name']}: {jockey['wins']}勝/{jockey['runs']}騎乗 (複勝率{jockey['fukusho_rate']:.1%})")
            
            print(f"\n【枠順傾向】")
            for position, stats in result['trends']['post_position_trend'].items():
                print(f"  {position}: 複勝率{stats['fukusho_rate']:.1%}")
            
            print(f"\n【馬場状態】")
            print(f"  状態: {result['trends']['track_condition']}")
            print(f"  バイアス: {result['trends']['track_bias']}")
            
            print(f"\n【推奨事項】")
            for rec in result['recommendations']:
                print(f"  ⭐ {rec}")
                
        else:
            print(f"❌ エラー: {result['message']}")
            
    except Exception as e:
        print(f"❌ 例外発生: {e}")
        import traceback
        traceback.print_exc()


def test_missing_horses():
    """存在しない馬でのテスト"""
    print_section("4. エラーハンドリングのテスト")
    
    race_data = {
        'venue': '東京',
        'race_number': 1,
        'race_name': 'テストレース',
        'horses': [
            '存在しない馬A',
            '存在しない馬B',
            '存在しない馬C'
        ]
    }
    
    try:
        engine = ViewLogicEngine()
        result = engine.predict_race_flow(race_data)
        
        if result['status'] == 'error':
            print(f"✅ 期待通りのエラー: {result['message']}")
        else:
            print("❌ エラーが期待されたが成功してしまった")
            
    except Exception as e:
        print(f"✅ 例外をキャッチ: {e}")


def main():
    """メイン実行関数"""
    print("\n" + "🏇"*30)
    print("  ViewLogicエンジン テストスイート")
    print("🏇"*30)
    
    # 各機能をテスト
    test_race_flow_prediction()
    test_course_trend_analysis()
    test_daily_trend_analysis()
    test_missing_horses()
    
    print("\n" + "="*60)
    print(" テスト完了")
    print("="*60)


if __name__ == "__main__":
    main()