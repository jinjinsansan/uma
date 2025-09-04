"""
統合ナレッジファイルの構造を確認するスクリプト
エアビッグマムとシェイクユアハートのデータ構造を比較
"""

import json
import sys
sys.path.insert(0, '/mnt/e/dev/Cusor/chatbot/uma/backend')

from services.dlogic_raw_data_manager import DLogicRawDataManager

# データマネージャーを初期化
manager = DLogicRawDataManager()

# テスト対象の馬
test_horses = ["エアビッグマム", "シェイクユアハート"]

for horse_name in test_horses:
    print(f"\n{'='*50}")
    print(f"馬名: {horse_name}")
    print('='*50)
    
    # 馬データを取得
    horse_data = manager.get_horse_raw_data(horse_name)
    
    if horse_data and horse_data.get('races'):
        # 直近のレースデータを確認
        race = horse_data['races'][0]
        
        print(f"\n最新レースの全フィールド（最初の20個）:")
        
        # すべてのキーを表示（最初の20個）
        for i, (key, value) in enumerate(race.items()):
            if i >= 20:
                break
            print(f"  {key}: '{value}'")
        
        # 重要なフィールドを個別に確認
        print(f"\n重要フィールド:")
        important_fields = [
            'KYOSOMEI_HONDAI', 
            'KYOSOMEI_FUKUSHO',
            'RACE_BANGO', 
            'GRADE_CODE',
            'TOKUBETSUKYOSO_CODE',
            'JYOKEN',
            'KAISAI_NEN',
            'KAISAI_GAPPI',
            'KEIBAJO_CODE'
        ]
        
        for field in important_fields:
            value = race.get(field, 'フィールドなし')
            print(f"  {field}: '{value}'")
    else:
        print(f"{horse_name}のデータが見つかりません")

print("\n\n分析完了")