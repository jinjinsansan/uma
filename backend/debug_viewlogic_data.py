#!/usr/bin/env python3
"""
ViewLogicのデータ形式を詳しく調査
"""

from services.viewlogic_data_manager import get_viewlogic_data_manager

def debug_data():
    """データ形式を詳しく調査"""
    
    # データマネージャー初期化
    manager = get_viewlogic_data_manager()
    
    # テスト馬のデータを取得
    test_horses = ['ドウデュース', 'イクイノックス', 'エフフォーリア']
    
    for horse_name in test_horses:
        print(f"\n{'='*60}")
        print(f"馬名: {horse_name}")
        print(f"{'='*60}")
        
        horse_data = manager.get_horse_data(horse_name)
        
        if horse_data and 'races' in horse_data:
            # 直近3レースのデータを詳しく表示
            for i, race in enumerate(horse_data['races'][:3]):
                print(f"\nレース{i+1}:")
                
                # 前半3Fと後半3Fのデータ
                zenhan = race.get('ZENHAN_3F', 'なし')
                kohan = race.get('KOHAN_3F', 'なし')
                
                print(f"  ZENHAN_3F（元データ）: {zenhan}")
                print(f"  KOHAN_3F（元データ）: {kohan}")
                
                # 型確認と変換テスト
                if zenhan != 'なし':
                    print(f"  型: {type(zenhan)}")
                    
                    # floatに変換
                    try:
                        zenhan_float = float(zenhan)
                        print(f"  float変換: {zenhan_float}")
                        
                        # 各種変換パターンをテスト
                        print(f"  /10: {zenhan_float / 10}秒")
                        print(f"  /100: {zenhan_float / 100}秒")
                        print(f"  そのまま: {zenhan_float}秒")
                    except Exception as e:
                        print(f"  変換エラー: {e}")
                
                # その他のフィールドも確認
                print(f"  KYORI（距離）: {race.get('KYORI', 'なし')}")
                print(f"  TRACK_CODE: {race.get('TRACK_CODE', 'なし')}")
                print(f"  KAISAI_NEN: {race.get('KAISAI_NEN', 'なし')}")
        else:
            print("データなし")

if __name__ == "__main__":
    debug_data()