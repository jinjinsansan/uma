#!/usr/bin/env python3
"""トラックコードの詳細調査"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

def investigate_track_codes():
    print("=" * 60)
    print("地方競馬トラックコード詳細調査")
    print("=" * 60)
    
    print("\n【PC-KEIBAのトラックコード定義（推定）】")
    print("  通常のJRAコード:")
    print("    10: 芝")
    print("    23: ダート")
    print("")
    print("  地方競馬特有のコード（可能性）:")
    print("    24: 地方ダート（良）?")
    print("    25: 地方ダート（稍重）?")
    print("    26: 地方ダート（重）?")
    print("    27: 地方ダート（不良）?")
    print("")
    print("  または:")
    print("    24-27: 各競馬場の特殊トラック?")
    print("")
    
    print("\n【観察されたパターン】")
    print("  船橋44 + トラックコード26: 多数")
    print("  船橋44 + トラックコード24: 少数")
    print("  大井42 + トラックコード23: 多数（通常）")
    print("")
    
    print("\n【問題の仮説】")
    print("1. データ取得時の競馬場コード誤り")
    print("   - シーソーゲームの実際の競馬場は大井（42）")
    print("   - なぜか船橋（44）として記録されている")
    print("")
    print("2. トラックコードの特殊性")
    print("   - 26、24は地方競馬特有のコード")
    print("   - 芝として解釈されているが実際はダート")
    print("")
    print("3. データソースの問題")
    print("   - PC-KEIBAのnvdテーブルのデータ自体が誤っている可能性")
    print("   - または取得時の変換ロジックに問題")
    
    # CDNファイルのデータ構造を詳しく確認
    from services.local_dlogic_raw_data_manager_v2 import local_dlogic_manager_v2
    
    print("\n【CDNファイルのデータ構造確認】")
    
    # シーソーゲームのデータを詳細確認
    horse_data = local_dlogic_manager_v2.get_horse_raw_data('シーソーゲーム')
    if horse_data:
        races = horse_data.get('races', [])
        print(f"\nシーソーゲーム: {len(races)}レース")
        
        for i, race in enumerate(races, 1):
            print(f"\n  レース{i}の全フィールド:")
            # 重要フィールドのみ表示
            important_fields = [
                'KAISAI_NEN', 'KAISAI_GAPPI', 'KEIBAJO_CODE', 'track_name',
                'RACE_BANGO', 'KYORI', 'TRACK_CODE', 'KAKUTEI_CHAKUJUN',
                'SHIBA_BABAJOTAI_CODE', 'DIRT_BABAJOTAI_CODE',
                'KISHUMEI_RYAKUSHO', 'ZENHAN_3F_TIME', 'KOHAN_3F_TIME'
            ]
            
            for field in important_fields:
                if field in race:
                    print(f"    {field}: {race[field]}")
    
    # 他の馬のトラックコード調査
    print("\n【他の馬のトラックコード分布】")
    track_code_dist = {}
    sample_count = 0
    
    for horse_name in ['リケアカプチーノ', 'ヴァンディヴェール', 'ネフェルトゥム']:
        horse_data = local_dlogic_manager_v2.get_horse_raw_data(horse_name)
        if horse_data:
            races = horse_data.get('races', [])
            print(f"\n  {horse_name}:")
            for race in races[:3]:
                track_code = race.get('TRACK_CODE', '??')
                keibajo = race.get('KEIBAJO_CODE', '??')
                track_name = race.get('track_name', '??')
                
                key = f"{keibajo}:{track_name}:TC{track_code}"
                track_code_dist[key] = track_code_dist.get(key, 0) + 1
                
                print(f"    {race.get('KAISAI_NEN')}年{race.get('KAISAI_GAPPI')[:2]}月: "
                      f"{track_name}({keibajo}) TC:{track_code}")
    
    print("\n【トラックコード分布】")
    for key, count in sorted(track_code_dist.items()):
        print(f"  {key}: {count}件")

if __name__ == "__main__":
    investigate_track_codes()