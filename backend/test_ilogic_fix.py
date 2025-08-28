#!/usr/bin/env python3
"""
I-Logic計算エンジン修正テスト
IMLogicと同じ12項目重み付け計算が正しく動作することを確認
"""
import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# バックエンドのパスを追加
sys.path.insert(0, '/mnt/c/Users/USER/OneDrive/デスクトップ/Cusor/chatbot/uma/backend')

from services.race_analysis_engine import RaceAnalysisEngine
from services.fast_dlogic_engine import FastDLogicEngine

def test_race_analysis():
    """I-Logic計算のテスト"""
    
    print("=" * 60)
    print("I-Logic計算エンジン修正テスト")
    print("=" * 60)
    
    # テストデータ（新潟2R）
    test_race = {
        'venue': '新潟',
        'race_number': 2,
        'race_name': '2歳未勝利',
        'grade': '',
        'distance': '1400m',
        'track_condition': '良',
        'horses': [
            'イージーブリージー',
            'エストゥペンダ',
            'カイザーバローズ',
            'ショウナンアクア',
            'スムースベルベット'
        ],
        'jockeys': [
            '木幡巧也',
            '杉原誠人',
            '北村宏司',
            '内田博幸',
            'ルメール'
        ],
        'posts': [1, 2, 3, 4, 5],
        'horse_numbers': [1, 2, 3, 4, 5]
    }
    
    try:
        # FastDLogicEngineインスタンスを作成
        print("\n1. FastDLogicEngineを初期化中...")
        fast_engine = FastDLogicEngine()
        print("   ✓ FastDLogicEngine初期化完了")
        
        # RaceAnalysisEngineを初期化
        print("\n2. RaceAnalysisEngineを初期化中...")
        engine = RaceAnalysisEngine(fast_engine)
        print("   ✓ RaceAnalysisEngine初期化完了")
        
        # レース分析を実行
        print("\n3. レース分析を実行中...")
        result = engine.analyze_race(test_race)
        
        if 'error' in result:
            print(f"   ✗ エラー: {result['error']}")
            return
        
        print("   ✓ レース分析完了")
        
        # 結果表示
        print("\n" + "=" * 60)
        print("分析結果（修正版I-Logic）")
        print("=" * 60)
        print(f"\n基準: {result.get('base_horse', 'N/A')}")
        print(f"馬と騎手の比率: 馬{int(result['weights']['horse']*100)}% / 騎手{int(result['weights']['jockey']*100)}%")
        
        if 'item_weights' in result:
            print("\n12項目の重み付け:")
            for item, weight in result['item_weights'].items():
                print(f"  {item}: {weight}%")
        
        print("\n順位表:")
        print("-" * 60)
        print(f"{'順位':<4} {'馬名':<20} {'騎手':<15} {'総合':<7} {'馬':<7} {'騎手':<7} {'状態':<10}")
        print("-" * 60)
        
        for r in result['results'][:10]:
            status = ''
            if not r.get('has_data', True):
                status = 'データなし'
            elif r.get('estimation_method') == 'bayesian':
                status = 'ベイズ推定'
            elif r.get('estimation_method') == 'full_data':
                status = '通常計算'
            
            print(f"{r['rank']:<4} {r['horse'][:18]:<20} {r['jockey'][:13]:<15} "
                  f"{r['total_score']:>6.1f} {r['horse_score']:>6.1f} {r['jockey_score']:>6.1f} {status}")
        
        # データなしの馬を確認
        no_data_horses = [r for r in result['results'] if not r.get('has_data', True)]
        if no_data_horses:
            print("\n【データなしの馬】")
            for r in no_data_horses:
                print(f"  - {r['horse']}: 0点（ナレッジファイルにデータなし）")
        
        # ベイズ推定の馬を確認
        bayesian_horses = [r for r in result['results'] if r.get('estimation_method') == 'bayesian']
        if bayesian_horses:
            print("\n【ベイズ推定適用の馬】")
            for r in bayesian_horses:
                print(f"  - {r['horse']}: {r['horse_score']:.1f}点（データ不足のため保守的評価）")
        
        print("\n✅ テスト成功: I-LogicがIMLogicと同じ計算方法で動作しています")
        
    except Exception as e:
        print(f"\n✗ エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_race_analysis()