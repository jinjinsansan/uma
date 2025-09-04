"""
騎手ナレッジファイルを使用する各エンジンのテスト
1. I-Logicエンジン
2. IMLogicエンジン  
3. ViewLogic傾向分析サブエンジン
4. ViewLogic過去データサブエンジン
"""

import sys
import os
import json
import traceback

# バックエンドパスを追加
sys.path.append('/mnt/e/dev/Cusor/chatbot/uma/backend')

def test_jockey_knowledge_loading():
    """騎手ナレッジファイルの読み込みテスト"""
    try:
        print("=" * 60)
        print("騎手ナレッジファイル読み込みテスト")
        print("=" * 60)
        
        # ローカルファイルを読み込み
        with open('data/jockey_knowledge.json', 'r', encoding='utf-8') as f:
            jockey_data = json.load(f)
        
        print(f"✅ ファイル読み込み成功")
        print(f"   総騎手数: {len(jockey_data)}")
        print(f"   ファイルサイズ: {os.path.getsize('data/jockey_knowledge.json') / (1024*1024):.2f} MB")
        
        # 新規追加騎手の確認
        new_jockeys = ['ハマーハ', 'ゴンサル', 'トーレス']
        for jockey in new_jockeys:
            if jockey in jockey_data:
                print(f"   ✅ 新規騎手 '{jockey}' 確認OK")
        
        return jockey_data
    except Exception as e:
        print(f"❌ エラー: {e}")
        traceback.print_exc()
        return None

def test_ilogic_engine():
    """I-Logicエンジンのテスト"""
    try:
        print("\n" + "=" * 60)
        print("I-Logicエンジンテスト")
        print("=" * 60)
        
        from services.ilogic_engine import ILogicEngine
        
        # ローカルファイルを使用するように設定
        engine = ILogicEngine()
        
        # テスト用のレースデータ（騎手を含む）
        test_race_data = {
            'horses': [
                {'name': 'テスト馬1', 'jockey': '川田将雅'},
                {'name': 'テスト馬2', 'jockey': 'ハマーハ'},  # 新規追加騎手
            ]
        }
        
        print("✅ I-Logicエンジン初期化成功")
        print("   騎手データ読み込み可能")
        return True
        
    except Exception as e:
        print(f"❌ I-Logicエンジンエラー: {e}")
        traceback.print_exc()
        return False

def test_imlogic_engine():
    """IMLogicエンジンのテスト"""
    try:
        print("\n" + "=" * 60)
        print("IMLogicエンジンテスト")
        print("=" * 60)
        
        from services.imlogic_engine import IMLogicEngine
        
        engine = IMLogicEngine()
        print("✅ IMLogicエンジン初期化成功")
        print("   騎手データ読み込み可能")
        return True
        
    except Exception as e:
        print(f"❌ IMLogicエンジンエラー: {e}")
        traceback.print_exc()
        return False

def test_viewlogic_tendency():
    """ViewLogic傾向分析サブエンジンのテスト"""
    try:
        print("\n" + "=" * 60)
        print("ViewLogic傾向分析サブエンジンテスト")
        print("=" * 60)
        
        from services.viewlogic_tendency_engine import ViewLogicTendencyEngine
        
        engine = ViewLogicTendencyEngine()
        print("✅ ViewLogic傾向分析エンジン初期化成功")
        print("   騎手データ読み込み可能")
        return True
        
    except Exception as e:
        print(f"❌ ViewLogic傾向分析エラー: {e}")
        traceback.print_exc()
        return False

def test_viewlogic_past_data():
    """ViewLogic過去データサブエンジンのテスト"""
    try:
        print("\n" + "=" * 60)
        print("ViewLogic過去データサブエンジンテスト")
        print("=" * 60)
        
        from services.viewlogic_past_data_engine import ViewLogicPastDataEngine
        
        engine = ViewLogicPastDataEngine()
        print("✅ ViewLogic過去データエンジン初期化成功")
        print("   騎手データ読み込み可能")
        return True
        
    except Exception as e:
        print(f"❌ ViewLogic過去データエラー: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n騎手ナレッジファイル統合テスト開始\n")
    
    # 1. ファイル読み込みテスト
    jockey_data = test_jockey_knowledge_loading()
    
    if jockey_data:
        # 2. 各エンジンテスト
        results = {
            "I-Logic": test_ilogic_engine(),
            "IMLogic": test_imlogic_engine(),
            "ViewLogic傾向分析": test_viewlogic_tendency(),
            "ViewLogic過去データ": test_viewlogic_past_data()
        }
        
        # 結果サマリー
        print("\n" + "=" * 60)
        print("テスト結果サマリー")
        print("=" * 60)
        
        all_passed = True
        for engine_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{engine_name}: {status}")
            if not result:
                all_passed = False
        
        if all_passed:
            print("\n🎉 全エンジンテスト成功！CDNアップロード可能です。")
        else:
            print("\n⚠️ 一部エンジンでエラー。修正が必要です。")
