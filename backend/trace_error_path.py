#!/usr/bin/env python3
"""
ViewLogicエラーの実行パスを完全トレース
どのコードパスでエラーが発生するかを特定
"""

import json
import sys
import traceback

def trace_all_execution_paths():
    """全ての実行パスをトレースしてエラー発生箇所を特定"""
    
    print("=== ViewLogicエラー実行パストレース ===\n")
    
    # 1. ViewLogicEngineの全メソッドをテスト
    print("1. ViewLogicEngine 全メソッドテスト")
    
    try:
        from services.viewlogic_engine import ViewLogicEngine
        
        engine = ViewLogicEngine()
        
        # テストレースデータ
        race_data = {
            'venue': '新潟',
            'distance': 1200,
            'track_type': '芝',
            'horses': ['テストホース1', 'テストホース2'],
            'jockeys': ['武豊', '川田'],
            'posts': [1, 2]
        }
        
        print("   analyze_course_trend テスト:")
        result = engine.analyze_course_trend(race_data)
        print("   ✅ 正常完了")
        
        print("   _analyze_jockeys_post_performance テスト:")
        result = engine._analyze_jockeys_post_performance(['武豊', '川田'], [1, 2])
        print("   ✅ 正常完了")
        
        print("   _analyze_jockeys_course_performance テスト:")
        result = engine._analyze_jockeys_course_performance(['武豊', '川田'], '新潟', 1200, '芝')
        print("   ✅ 正常完了")
        
    except Exception as e:
        print(f"   ❌ ViewLogicEngineでエラー: {e}")
        traceback.print_exc()
    
    # 2. JockeyKnowledgeManagerの全メソッドをテスト
    print("\n2. JockeyKnowledgeManager 全メソッドテスト")
    
    try:
        from services.jockey_knowledge_manager import JockeyKnowledgeManager
        
        manager = JockeyKnowledgeManager()
        
        print("   get_jockey_post_position_fukusho_rates テスト:")
        result = manager.get_jockey_post_position_fukusho_rates(['武豊', '川田'])
        print(f"   ✅ 正常完了: {len(result)}名")
        
        print("   get_post_position_stats テスト:")
        result = manager.get_post_position_stats('武豊')
        print(f"   ✅ 正常完了: {type(result)}")
        
        print("   get_jockey_data テスト:")
        result = manager.get_jockey_data('武豊')
        print(f"   ✅ 正常完了: {type(result)}")
        
    except Exception as e:
        print(f"   ❌ JockeyKnowledgeManagerでエラー: {e}")
        traceback.print_exc()
    
    # 3. V2 AIハンドラーの実行パスをテスト
    print("\n3. V2 AIハンドラー実行パステスト")
    
    try:
        # V2のAIハンドラーをインポート
        sys.path.append('/mnt/c/Users/USER/OneDrive/デスクトップ/Cusor/chatbot/uma/backend/services/v2')
        from ai_handler import V2AIHandler
        
        handler = V2AIHandler()
        
        # ViewLogic分析をテスト
        test_message = "このレースの傾向分析して"
        race_data = {
            'venue': '新潟',
            'distance': 1200,
            'track_type': '芝',
            'horses': ['テストホース1', 'テストホース2'],
            'jockeys': ['武豊', '川田'],
            'posts': [1, 2]
        }
        
        print("   V2AIHandler ViewLogic分析テスト:")
        # handler.handle_message のテスト（実際のコードパス）
        response = handler.handle_message(test_message, race_data, 'viewlogic')
        print("   ✅ V2AIHandler正常完了")
        
    except Exception as e:
        print(f"   ❌ V2AIHandlerでエラー: {e}")
        
        # スタックトレースから詳細情報を抽出
        tb = traceback.format_exc()
        lines = tb.split('\n')
        
        print(f"   エラータイプ: {type(e).__name__}")
        print(f"   エラーメッセージ: {str(e)}")
        
        # 'get'メソッドが呼ばれている行を特定
        for i, line in enumerate(lines):
            if "'int' object has no attribute 'get'" in line or 'get' in line and 'int' in line:
                print(f"\n   🎯 エラー発生行特定:")
                # 前後の行も表示
                for j in range(max(0, i-3), min(len(lines), i+3)):
                    prefix = "   -> " if j == i else "      "
                    print(f"{prefix}{lines[j]}")
                break
        
        print(f"\n   完全スタックトレース:")
        traceback.print_exc()
    
    # 4. 異なる騎手名パターンでテスト
    print("\n4. 騎手名パターン別テスト")
    
    try:
        from services.jockey_knowledge_manager import JockeyKnowledgeManager
        manager = JockeyKnowledgeManager()
        
        # 様々な騎手名パターンをテスト
        test_patterns = [
            ['武豊', '川田'],
            ['武豊　', '川田将'],  # スペース付き
            ['武豊　　', '川田将雅'],  # スペース2つ付き
            ['存在しない騎手', '武豊'],  # 存在しない騎手を含む
            [],  # 空リスト
            ['武豊'] * 10,  # 同じ騎手を繰り返し
        ]
        
        for i, pattern in enumerate(test_patterns, 1):
            print(f"   パターン{i}: {pattern}")
            try:
                result = manager.get_jockey_post_position_fukusho_rates(pattern)
                print(f"      ✅ 正常完了: {len(result)}名")
            except Exception as e:
                print(f"      ❌ エラー: {e}")
                if "'int' object has no attribute 'get'" in str(e):
                    print(f"      🚨 target error reproduced!")
                    traceback.print_exc()
                    break
    
    except Exception as e:
        print(f"   騎手名パターンテスト全体でエラー: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    trace_all_execution_paths()
    print("\n=== 実行パストレース完了 ===")