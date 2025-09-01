#!/usr/bin/env python3
"""
ViewLogicナレッジファイルのデータ構造を確認
"""

from services.viewlogic_data_manager import get_viewlogic_data_manager
import json

def check_data_structure():
    """ViewLogicナレッジファイルのデータ構造を確認"""
    
    # データマネージャーを取得
    manager = get_viewlogic_data_manager()
    
    print("=== ViewLogicナレッジファイルのデータ構造確認 ===\n")
    
    # メタデータを確認
    metadata = manager.get_metadata()
    if metadata:
        print("【メタデータ】")
        print(f"生成日: {metadata.get('generated_at', '不明')}")
        print(f"総馬数: {metadata.get('total_horses', '不明')}")
        print(f"データ期間: {metadata.get('data_period', '不明')}")
        print()
    
    # 馬数を確認
    total_horses = manager.get_total_horses()
    print(f"【読み込み済み馬数】: {total_horses}頭\n")
    
    # サンプルとして最初の馬のデータ構造を確認
    sample_horse = None
    for horse_name, horse_data in list(manager.horses_dict.items())[:1]:
        sample_horse = horse_data
        print(f"【サンプル馬: {horse_name}】")
        print(f"データ構造:")
        
        # トップレベルのキーを表示
        for key in horse_data.keys():
            print(f"  - {key}: {type(horse_data[key]).__name__}")
        
        # racesの中身を確認
        if 'races' in horse_data and horse_data['races']:
            print(f"\n【races配列の最初のレースデータ】")
            first_race = horse_data['races'][0]
            
            # ZENHAN_3FとKOHAN_3Fを重点的に確認
            print("\n重要フィールドの値:")
            important_fields = ['ZENHAN_3F', 'KOHAN_3F', 'CORNER1_JUNI', 'CORNER2_JUNI', 
                              'CORNER3_JUNI', 'CORNER4_JUNI', 'KAKUTEI_CHAKUJUN']
            
            for field in important_fields:
                if field in first_race:
                    value = first_race[field]
                    print(f"  {field}: {value} (型: {type(value).__name__})")
                    
                    # 値の範囲を判定
                    if field in ['ZENHAN_3F', 'KOHAN_3F'] and isinstance(value, (int, float)):
                        if value >= 100:
                            print(f"    → 0.1秒単位のデータ（{value/10:.1f}秒）")
                        elif value < 100 and value > 0:
                            print(f"    → 秒単位のデータ（{value:.1f}秒）")
            
            # すべてのフィールドを表示
            print("\n全フィールド一覧:")
            for field_name in sorted(first_race.keys()):
                print(f"  - {field_name}")
    
    # 複数の馬でZENHAN_3F, KOHAN_3Fの値の分布を確認
    print("\n【前半3F・後半3Fの値の分布（最初の10頭）】")
    for i, (horse_name, horse_data) in enumerate(list(manager.horses_dict.items())[:10]):
        if 'races' in horse_data and horse_data['races']:
            first_race = horse_data['races'][0]
            zenhan = first_race.get('ZENHAN_3F', 'なし')
            kohan = first_race.get('KOHAN_3F', 'なし')
            print(f"{horse_name}: 前半3F={zenhan}, 後半3F={kohan}")

if __name__ == "__main__":
    check_data_structure()