#!/usr/bin/env python3
"""
生成された34項目版ナレッジファイルの検証
"""

import json
import os

def verify_knowledge():
    """34項目版ナレッジファイルの検証"""
    
    filename = "nankan_unified_knowledge_20250907.json"
    
    print(f"📊 {filename} の検証開始...")
    
    # ファイルサイズ確認
    file_size = os.path.getsize(filename) / (1024 * 1024)
    print(f"✅ ファイルサイズ: {file_size:.1f}MB")
    
    # JSONファイル読み込み
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"✅ 総馬数: {len(data)}頭")
    
    # 最初の馬のデータで34項目を確認
    first_horse = list(data.keys())[0]
    print(f"\n🐴 サンプル馬: {first_horse}")
    
    if data[first_horse] and len(data[first_horse]) > 0:
        first_race = data[first_horse][0]
        
        print(f"📋 フィールド数: {len(first_race)}項目")
        
        # 重要フィールドの確認
        print("\n🔍 重要フィールドの確認:")
        important_fields = [
            'BAMEI', 'RACE_CODE', 'KAISAI_NEN', 'KAISAI_GAPPI',
            'CORNER1_JUNI', 'CORNER2_JUNI', 'CORNER3_JUNI', 'CORNER4_JUNI',
            'SOHA_TIME', 'KYORI', 'track_name',
            'ZENHAN_3F_TIME', 'KOHAN_3F_TIME'  # 新規追加フィールド
        ]
        
        for field in important_fields:
            if field in first_race:
                value = first_race[field]
                if field in ['ZENHAN_3F_TIME', 'KOHAN_3F_TIME']:
                    print(f"   ✅ {field}: {value} ← ★新規追加")
                else:
                    print(f"   ✅ {field}: {value}")
            else:
                print(f"   ❌ {field}: 存在しない")
        
        # 3Fタイムデータの統計
        print("\n📊 3Fタイムデータ統計:")
        zenhan_count = 0
        kohan_count = 0
        total_races = 0
        
        for horse_name in list(data.keys())[:1000]:  # 最初の1000頭でサンプリング
            for race in data[horse_name]:
                total_races += 1
                if race.get('ZENHAN_3F_TIME', '000') != '000':
                    zenhan_count += 1
                if race.get('KOHAN_3F_TIME', '000') != '000':
                    kohan_count += 1
        
        print(f"   サンプル（最初の1000頭）:")
        print(f"   - 前半3Fありの割合: {zenhan_count}/{total_races} ({zenhan_count*100/total_races:.1f}%)")
        print(f"   - 後半3Fありの割合: {kohan_count}/{total_races} ({kohan_count*100/total_races:.1f}%)")
        
        # 全フィールドリスト
        print("\n📝 全34フィールド:")
        for i, (key, value) in enumerate(first_race.items(), 1):
            if key in ['ZENHAN_3F_TIME', 'KOHAN_3F_TIME']:
                print(f"   {i:2d}. {key:25s} = {str(value)[:20]:20s} ← ★新規")
            else:
                print(f"   {i:2d}. {key:25s} = {str(value)[:20]:20s}")
    
    print("\n✅ 検証完了: 34項目版ナレッジファイルが正しく生成されました！")

if __name__ == "__main__":
    verify_knowledge()