#!/usr/bin/env python3
"""
騎手ナレッジファイルのデータ構造と騎手名の調査
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.jockey_knowledge_manager import JockeyKnowledgeManager

def debug_jockey_data():
    """騎手ナレッジファイルのデータを調査"""
    
    print("🔍 騎手ナレッジファイル詳細調査")
    print("=" * 50)
    
    # 騎手マネージャー初期化
    manager = JockeyKnowledgeManager()
    
    if not manager.is_loaded():
        print("❌ 騎手データが読み込まれていません")
        return
    
    print(f"✅ 騎手データ読み込み完了: {len(manager.jockey_data)}騎手")
    print()
    
    # テスト対象騎手名
    test_jockeys = [
        '川田将雅',
        '川田',
        '武豊',
        '武豊　',
        '武豊　　',
        'ルメール',
        'C.ルメール',
        '横山武史'
    ]
    
    print("📋 テスト騎手名の検索結果:")
    for jockey_name in test_jockeys:
        data = manager.get_jockey_data(jockey_name)
        if data:
            print(f"✅ 「{jockey_name}」: データあり")
        else:
            print(f"❌ 「{jockey_name}」: データなし")
    
    print()
    print("🔍 実際の騎手名リスト（川田・武豊・ルメール・横山を含む）:")
    
    found_names = []
    for name in manager.jockey_data.keys():
        if any(target in name for target in ['川田', '武豊', 'ルメール', '横山武']):
            found_names.append(name)
    
    for name in sorted(found_names):
        print(f"  - 「{name}」 (長さ: {len(name)})")
        # 文字コードも表示
        chars = [f"{c}({ord(c)})" for c in name]
        print(f"    文字コード: {' '.join(chars[:10])}...")
    
    print()
    print("📊 騎手ナレッジファイルの全騎手名（先頭20名）:")
    all_names = list(manager.jockey_data.keys())[:20]
    for i, name in enumerate(all_names):
        print(f"  {i+1:2d}. 「{name}」 (長さ: {len(name)})")
    
    print()
    print(f"📈 総騎手数: {len(manager.jockey_data)}")
    
    # ViewLogicエンジンの正規化メソッドもテスト
    print()
    print("🔧 ViewLogicエンジンの正規化テスト:")
    from services.viewlogic_engine import ViewLogicEngine
    
    try:
        engine = ViewLogicEngine()
        
        for jockey_name in ['川田将雅', '武豊', 'C.ルメール']:
            normalized = engine._normalize_jockey_name(jockey_name)
            print(f"  「{jockey_name}」 → 「{normalized}」")
            
            # 正規化後のデータ取得テスト
            data = manager.get_jockey_data(normalized)
            if data:
                print(f"    ✅ 正規化後データあり")
            else:
                print(f"    ❌ 正規化後もデータなし")
    
    except Exception as e:
        print(f"❌ ViewLogicエンジン初期化エラー: {e}")

if __name__ == "__main__":
    debug_jockey_data()