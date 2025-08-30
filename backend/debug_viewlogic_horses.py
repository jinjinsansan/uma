#!/usr/bin/env python3
"""
ViewLogic傾向分析の馬データ取得問題をデバッグ
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.viewlogic_data_manager import get_viewlogic_data_manager
import json

def debug_horses():
    """馬データの詳細をデバッグ"""
    
    print("ViewLogicデータマネージャー初期化中（シングルトン）...")
    manager = get_viewlogic_data_manager()
    
    if not manager.is_loaded():
        print("❌ データが読み込まれていません")
        return
    
    print(f"✅ {manager.get_total_horses()}頭のデータを読み込みました")
    
    # テスト馬のリスト（実際のレースデータから）
    test_horses = [
        'ケアンズトーラス',
        'カバーガール',
        'リメイク',
        'マンハッタンロック',
        'レオアスク',
        'トミケンカラバティ',
        'テオリア',
        'テネレッツァ',
        'ファクトベース',
        'トランセンデンス',
        'クリノセレブ',
        'タケルアムール',
        'ホープウィッシュ',
        'カイアワセ',
        'アイラナンバーワン',
        'オールマイワーズ',
        'スラージュ',
        'フロスティグレイ'
    ]
    
    print("\n=== 馬データ存在確認 ===")
    found_count = 0
    niigata_1200_count = 0
    
    for horse_name in test_horses:
        horse_data = manager.get_horse_data(horse_name)
        
        if horse_data:
            found_count += 1
            print(f"✅ {horse_name}: データあり", end="")
            
            # 新潟1200mのレースがあるか確認
            if 'races' in horse_data:
                niigata_races = 0
                for race in horse_data['races']:
                    if race.get('KEIBAJO_CODE') == '04':  # 新潟
                        kyori = race.get('KYORI')
                        if kyori:
                            try:
                                if abs(int(kyori) - 1200) <= 100:
                                    niigata_races += 1
                            except:
                                pass
                
                if niigata_races > 0:
                    niigata_1200_count += 1
                    print(f" → 新潟1200m: {niigata_races}レース")
                else:
                    print()
            else:
                print(" (racesフィールドなし)")
        else:
            print(f"❌ {horse_name}: データなし")
    
    print(f"\n=== 統計 ===")
    print(f"データあり: {found_count}/{len(test_horses)}頭")
    print(f"新潟1200m経験馬: {niigata_1200_count}頭")
    
    # 問題の診断
    print("\n=== 診断結果 ===")
    if found_count == 0:
        print("❌ 全馬のデータが見つかりません → データマネージャーの初期化問題")
    elif niigata_1200_count == 0:
        print("⚠️ 新潟1200m経験馬が0頭 → 技術的には正しいが、ユーザーの期待と異なる")
    else:
        print(f"✅ {niigata_1200_count}頭が新潟1200m経験あり → コードは正常に動作している")

if __name__ == "__main__":
    debug_horses()