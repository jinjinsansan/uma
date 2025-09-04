"""
統合ナレッジファイルの生データを直接確認
"""

import json
import sys
sys.path.insert(0, '/mnt/e/dev/Cusor/chatbot/uma/backend')

from services.viewlogic_data_manager import ViewLogicDataManager

# データマネージャーを初期化
manager = ViewLogicDataManager()

# テスト対象の馬
test_horses = ["エアビッグマム", "シェイクユアハート"]

for horse_name in test_horses:
    print(f"\n{'='*50}")
    print(f"馬名: {horse_name}")
    print('='*50)
    
    # 生データを取得
    if horse_name in manager.horses_dict:
        horse_data = manager.horses_dict[horse_name]
        
        if horse_data and 'races' in horse_data:
            race = horse_data['races'][0]
            
            print(f"\n最新レースの重要フィールド:")
            
            # レース名関連のフィールドをすべて探す
            for key in race.keys():
                if 'KYOSO' in key.upper() or 'RACE' in key.upper() or 'GRADE' in key.upper() or 'レース' in str(race[key]):
                    print(f"  {key}: '{race[key]}'")
            
            print(f"\nKYOSOMEI_HONDAI: '{race.get('KYOSOMEI_HONDAI', 'なし')}'")
            print(f"GRADE_CODE: '{race.get('GRADE_CODE', 'なし')}'")
            
            # 全フィールドの最初の30個を表示
            print(f"\n全フィールド（最初の30個）:")
            for i, (key, value) in enumerate(race.items()):
                if i >= 30:
                    break
                if value and str(value).strip():
                    print(f"  {key}: '{value}'")