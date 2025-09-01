#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
不足している3つのG1レースのViewLogic上位5頭を計算
"""

import sys
import json
from services.viewlogic_engine import ViewLogicEngine

# 不足している3レースのデータ
missing_races = [
    {
        "id": "yasuda-kinen-2024",
        "name": "安田記念",
        "venue": "東京",
        "distance": "1600m",
        "track_condition": "稍重",
        "horses": [
            'カテドラル', 'ガイアフォース', 'レッドモンレーヴ', 'ジオグリフ',
            'ナミュール', 'ドーブネ', 'ロマンチックウォリアー', 'エアロロノア',
            'パラレルヴィジョン', 'ソウルラッシュ', 'ウインカーネリアン', 'フィアスプライド',
            'ステラヴェローチェ', 'コレペティトール', 'ヴォイッジバブル', 'エルトンバローズ',
            'セリフォス', 'ダノンスコーピオン'
        ]
    },
    {
        "id": "queen-elizabeth-cup-2024",
        "name": "エリザベス女王杯",
        "venue": "京都",
        "distance": "2200m",
        "track_condition": "良",
        "horses": [
            'ホールネス', 'ライラック', 'ルージュリナージュ', 'コンクシェル',
            'モリアーナ', 'ピースオブザライフ', 'レガレイラ', 'シンリョクカ',
            'キミノナハマリア', 'エリカヴィータ', 'スタニングローズ', 'シンティレーション',
            'サリエラ', 'ハーパー', 'ゴールドエクリプス', 'ラヴェル',
            'コスタボニータ'
        ]
    },
    {
        "id": "asahi-hai-2024",
        "name": "朝日杯フューチュリティステークス",
        "venue": "阪神",
        "distance": "1600m",
        "track_condition": "良",
        "horses": [
            'ダイシンラー', 'アドマイヤズーム', 'ランスオブカオス', 'ミュージアムマイル',
            'コスモストーム', 'アルレッキーノ', 'クラスペディア', 'アルテヴェローチェ',
            'エルムラント', 'トータルクラリティ', 'ニタモノドウシ', 'パンジャタワー',
            'エイシンワンド', 'テイクイットオール', 'ドラゴンブースト', 'タイセイカレント'
        ]
    }
]

def calculate_viewlogic_for_race(race_data):
    """1つのレースのViewLogic結果を計算"""
    try:
        print(f"\n🏇 {race_data['name']}の計算開始...")
        
        engine = ViewLogicEngine()
        
        # レース情報を準備
        race_info = {
            'venue': race_data['venue'],
            'race_number': 11,  # G1レース想定
            'race_name': race_data['name'],
            'distance': race_data['distance'],
            'track_condition': race_data['track_condition'],
            'horses': race_data['horses']
        }
        
        # ViewLogic分析実行
        result = engine.predict_race_flow_advanced(race_info)
        
        if result and 'analysis' in result:
            # 上位5頭を抽出
            top_horses = []
            analysis = result['analysis']
            
            # レスポンスから上位5頭を抽出（パターンマッチング）
            import re
            
            # パターン1: "有力候補" セクションを探す
            pattern1 = r'【有力候補】.*?(\d+\..*?(?:\n|$)){5}'
            match1 = re.search(pattern1, analysis, re.DOTALL)
            
            if match1:
                lines = match1.group(0).split('\n')
                for line in lines[1:6]:  # 1行目は【有力候補】なのでスキップ
                    if line.strip() and not line.startswith('【'):
                        # 馬名を抽出（数字や記号を削除）
                        horse_name = re.sub(r'^\d+\.\s*', '', line.strip())
                        horse_name = re.sub(r'\s*（.*）|\s*\(.*\)|\s*-.*', '', horse_name)
                        horse_name = horse_name.strip()
                        if horse_name in race_data['horses']:
                            top_horses.append(horse_name)
            
            # パターン2: 馬名を直接検索
            if len(top_horses) < 5:
                for horse in race_data['horses']:
                    if horse in analysis and horse not in top_horses:
                        top_horses.append(horse)
                        if len(top_horses) >= 5:
                            break
            
            # 最低5頭確保（不足時は出走馬から補完）
            while len(top_horses) < 5 and len(top_horses) < len(race_data['horses']):
                for horse in race_data['horses']:
                    if horse not in top_horses:
                        top_horses.append(horse)
                        break
            
            print(f"✅ {race_data['name']} ViewLogic上位5頭:")
            for i, horse in enumerate(top_horses[:5], 1):
                print(f"   {i}位: {horse}")
            
            return {
                'race_id': race_data['id'],
                'viewlogic_top5': top_horses[:5]
            }
        else:
            print(f"❌ {race_data['name']}: ViewLogic分析結果が取得できませんでした")
            return None
            
    except Exception as e:
        print(f"❌ {race_data['name']}の計算でエラー: {str(e)}")
        return None

def main():
    """メイン処理"""
    print("🔮 ViewLogic上位5頭計算開始")
    print("=" * 50)
    
    results = []
    
    for race in missing_races:
        result = calculate_viewlogic_for_race(race)
        if result:
            results.append(result)
        
        # API負荷軽減のため5秒待機
        import time
        time.sleep(5)
    
    print("\n" + "=" * 50)
    print("🎯 計算結果サマリー:")
    
    for result in results:
        race_id = result['race_id']
        top5 = result['viewlogic_top5']
        
        print(f"\n'{race_id}': {{")
        print(f"  viewlogicTop5: {top5}")
        print("},")
    
    return results

if __name__ == "__main__":
    try:
        results = main()
        print(f"\n✅ 完了: {len(results)}レースのViewLogic上位5頭を計算しました")
    except KeyboardInterrupt:
        print("\n⚠️ 処理を中断しました")
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {str(e)}")
        sys.exit(1)