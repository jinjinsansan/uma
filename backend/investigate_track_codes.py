#!/usr/bin/env python3
"""競馬場コードとトラックコードのマッピングを調査"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from services.local_dlogic_raw_data_manager_v2 import local_dlogic_manager_v2
import json

def investigate_track_codes():
    print("=" * 60)
    print("競馬場コードマッピング調査")
    print("=" * 60)
    
    # 南関東の競馬場コード（一般的な定義）
    print("\n【一般的な地方競馬場コード】")
    print("  42: 大井")
    print("  43: 川崎")
    print("  44: 船橋")
    print("  45: 浦和")
    
    # CDNファイルの情報を確認
    print("\n【CDNファイル情報】")
    print(f"  URL: {local_dlogic_manager_v2.cdn_url}")
    
    # ナレッジデータの構造を確認
    if hasattr(local_dlogic_manager_v2, 'knowledge_data'):
        horses = local_dlogic_manager_v2.knowledge_data.get('horses', {})
        print(f"  総馬数: {len(horses)}頭")
        
        # メタデータを確認
        metadata = local_dlogic_manager_v2.knowledge_data.get('metadata', {})
        if metadata:
            print("\n【メタデータ】")
            for key, value in metadata.items():
                print(f"  {key}: {value}")
        
        # シーソーゲーム以外の馬のデータも少し確認
        print("\n【他の馬のデータサンプル（競馬場確認）】")
        sample_count = 0
        track_stats = {}
        
        for horse_name, horse_data in horses.items():
            if sample_count >= 100:  # 100頭分をサンプリング
                break
            
            # horse_dataがリストの場合は最初の要素を取得    
            if isinstance(horse_data, list):
                races = horse_data
            else:
                races = horse_data.get('races', [])
            for race in races:
                track_code = race.get('KEIBAJO_CODE', 'unknown')
                track_name = race.get('track_name', 'unknown')
                track_type = race.get('TRACK_CODE', 'unknown')
                
                key = f"{track_code}:{track_name}:トラック{track_type}"
                track_stats[key] = track_stats.get(key, 0) + 1
                
            sample_count += 1
        
        print("\n【競馬場別レース数統計】")
        for track_info, count in sorted(track_stats.items(), key=lambda x: x[1], reverse=True)[:20]:
            print(f"  {track_info}: {count}レース")
    
    # トラックコードの意味を調査
    print("\n【トラックコード解析】")
    print("  通常の定義:")
    print("    23: ダート")
    print("    その他: 芝または特殊")
    
    # 実際のデータパターンを確認
    track_code_patterns = {}
    sample_horses = ['シーソーゲーム', 'リケアカプチーノ', 'ナチュラルライズ']
    
    for horse_name in sample_horses:
        horse_data = local_dlogic_manager_v2.get_horse_raw_data(horse_name)
        if horse_data:
            print(f"\n  {horse_name}のトラックコード:")
            races = horse_data.get('races', [])
            for i, race in enumerate(races[:3], 1):
                track_code = race.get('TRACK_CODE', '??')
                track_name = race.get('track_name', '??')
                keibajo_code = race.get('KEIBAJO_CODE', '??')
                print(f"    レース{i}: 競馬場コード{keibajo_code}({track_name}) - トラックコード{track_code}")

if __name__ == "__main__":
    investigate_track_codes()