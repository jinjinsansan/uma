#!/usr/bin/env python3
"""
D-Logicナレッジの血統情報を確認
"""
from services.fast_dlogic_engine import fast_engine_instance

# D-Logicのナレッジデータを確認
if fast_engine_instance and fast_engine_instance.raw_manager:
    knowledge = fast_engine_instance.raw_manager.knowledge_data.get('horses', {})
    
    # イクイノックスのデータを確認
    horse_name = "イクイノックス"
    if horse_name in knowledge:
        horse_data = knowledge[horse_name]
        print(f"{horse_name}のD-Logicナレッジデータ構造:")
        print(f"データ型: {type(horse_data)}")
        print(f"キー: {list(horse_data.keys())}")
        
        # racesデータを確認
        if 'races' in horse_data:
            races = horse_data['races']
            print(f"\nレース数: {len(races)}")
            if len(races) > 0:
                print(f"\n最新レースのデータ:")
                latest_race = races[0]
                print(f"レースデータのキー: {list(latest_race.keys())}")
                
                # 血統関連フィールドを確認
                print(f"\n血統関連データ:")
                print(f"父馬 (sire): '{latest_race.get('sire', 'なし')}'")
                print(f"母馬 (dam): '{latest_race.get('dam', 'なし')}'")
                print(f"母父馬 (broodmare_sire): '{latest_race.get('broodmare_sire', 'なし')}'")
    else:
        print(f"{horse_name}のデータが見つかりません")
    
    # サンプル馬でも確認
    print("\n=== 他の馬の血統データも確認 ===")
    sample_horses = list(knowledge.keys())[:3]
    for horse in sample_horses:
        if 'races' in knowledge[horse] and len(knowledge[horse]['races']) > 0:
            race = knowledge[horse]['races'][0]
            print(f"\n{horse}:")
            print(f"  父馬: '{race.get('sire', 'なし')}'")
            print(f"  母馬: '{race.get('dam', 'なし')}'")
            print(f"  母父馬: '{race.get('broodmare_sire', 'なし')}'")
else:
    print("D-Logicエンジンが初期化されていません")