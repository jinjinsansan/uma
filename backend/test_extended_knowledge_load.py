#!/usr/bin/env python3
"""
拡張ナレッジファイルの読み込みテスト
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.extended_knowledge_manager import get_extended_knowledge_manager

def test_load():
    """拡張ナレッジの読み込みをテスト"""
    print("=== 拡張ナレッジファイル読み込みテスト ===\n")
    
    try:
        # マネージャーを取得
        manager = get_extended_knowledge_manager()
        
        # データ確認
        horses = manager.get_all_horses()
        print(f"✅ 拡張ナレッジ読み込み成功")
        print(f"   総馬数: {len(horses)}頭")
        
        # サンプルデータ確認
        sample_horses = list(horses.keys())[:5]
        print(f"\nサンプル馬:")
        for horse in sample_horses:
            data = horses[horse]
            if isinstance(data, list):
                print(f"  - {horse}: {len(data)}レース")
            elif isinstance(data, dict):
                races = data.get('races', [])
                print(f"  - {horse}: {len(races)}レース")
        
        # イクイノックスの確認
        if "イクイノックス" in horses:
            equinox_data = horses["イクイノックス"]
            if isinstance(equinox_data, list):
                print(f"\n✅ イクイノックス: {len(equinox_data)}レース")
            else:
                print(f"\n✅ イクイノックス: {len(equinox_data.get('races', []))}レース")
        else:
            print("\n❌ イクイノックスが見つかりません")
            
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_load()