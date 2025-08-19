#!/usr/bin/env python3
"""
拡張ナレッジファイルの読み込みテスト
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.extended_knowledge_manager import get_extended_knowledge_manager
import json

def test_extended_knowledge():
    """拡張ナレッジデータのロードと形式確認"""
    print("=== 拡張ナレッジファイル確認テスト ===\n")
    
    try:
        # マネージャー取得
        print("1. 拡張ナレッジマネージャー初期化...")
        manager = get_extended_knowledge_manager()
        
        # データ取得
        print("\n2. 全馬データ取得...")
        all_horses = manager.get_all_horses()
        
        print(f"\n3. データ概要:")
        print(f"  総頭数: {len(all_horses)}")
        
        # データ形式確認
        if all_horses:
            # 最初の5頭のデータ形式を確認
            horse_names = list(all_horses.keys())[:5]
            print(f"  サンプル馬名: {horse_names}")
            
            for horse_name in horse_names[:2]:
                horse_data = all_horses[horse_name]
                print(f"\n  {horse_name}のデータ形式:")
                print(f"    タイプ: {type(horse_data)}")
                
                if isinstance(horse_data, list):
                    print(f"    レース数: {len(horse_data)}")
                    if horse_data:
                        print(f"    最初のレースのキー: {list(horse_data[0].keys())[:5]}")
                elif isinstance(horse_data, dict):
                    print(f"    キー: {list(horse_data.keys())}")
                    if 'races' in horse_data:
                        print(f"    レース数: {len(horse_data['races'])}")
        
        # 特定の馬で詳細確認
        test_horses = ['イクイノックス', 'ドウデュース', 'プログノーシス']
        print(f"\n4. 特定馬の確認:")
        for horse in test_horses:
            if horse in all_horses:
                print(f"  {horse}: 存在する（データ形式: {type(all_horses[horse])}）")
            else:
                print(f"  {horse}: 存在しない")
                
    except Exception as e:
        print(f"\nエラー発生: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_extended_knowledge()