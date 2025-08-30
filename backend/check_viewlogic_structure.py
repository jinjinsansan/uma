#!/usr/bin/env python3
"""
ViewLogicナレッジファイルの構造を確認するスクリプト
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.viewlogic_data_manager import ViewLogicDataManager
import json

def check_structure():
    """ナレッジファイル構造を確認"""
    
    print("ViewLogicデータマネージャー初期化中...")
    manager = ViewLogicDataManager()
    
    if not manager.is_loaded():
        print("❌ データが読み込まれていません")
        return
    
    print(f"✅ {manager.get_total_horses()}頭のデータを読み込みました")
    
    # テスト馬のリスト
    test_horses = [
        'ケアンズトーラス',
        'カバーガール', 
        'リメイク',
        'ジュリスタ',
        'ミラコレジェンヌ',
        'シンフォニーシーズ'
    ]
    
    print("\n=== 馬データ構造の確認 ===")
    for horse_name in test_horses:
        horse_data = manager.get_horse_data(horse_name)
        
        if horse_data:
            print(f"\n【{horse_name}】データあり")
            print(f"  キー: {list(horse_data.keys())[:10]}...")  # 最初の10個のキーを表示
            
            # racesフィールドの確認
            if 'races' in horse_data:
                races = horse_data['races']
                print(f"  races: {len(races)}レース分のデータ")
                if races and len(races) > 0:
                    print(f"  最初のレースのキー: {list(races[0].keys())[:5]}...")
            else:
                print(f"  ⚠️ racesフィールドなし")
                
            # その他の重要フィールド
            if 'running_style' in horse_data:
                print(f"  running_style: {horse_data['running_style']}")
            if 'statistics' in horse_data:
                print(f"  statistics: あり")
            
            # 新潟1200m芝のレースがあるか確認
            niigata_count = 0
            if 'races' in horse_data:
                for race in horse_data['races']:
                    if race.get('KEIBAJO_CODE') == '04':  # 新潟
                        kyori = race.get('KYORI')
                        if kyori and abs(int(kyori) - 1200) <= 100:
                            niigata_count += 1
                            print(f"    → 新潟{kyori}mのレースあり")
            if niigata_count > 0:
                print(f"  ✅ 新潟1200m付近: {niigata_count}レース")
                
        else:
            print(f"\n【{horse_name}】データなし ❌")
    
    # メタデータの確認
    print("\n=== メタデータ ===")
    metadata = manager.get_metadata()
    if metadata:
        print(f"メタデータ: {json.dumps(metadata, ensure_ascii=False, indent=2)}")
    else:
        print("メタデータなし")

if __name__ == "__main__":
    check_structure()