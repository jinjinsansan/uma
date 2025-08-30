#!/usr/bin/env python3
"""
Renderデプロイメント状況の完全調査
エラーの正確な発生源を特定
"""

import traceback
import sys
import os

print("=== Renderデプロイメント調査 ===")
print(f"Python実行パス: {sys.executable}")
print(f"作業ディレクトリ: {os.getcwd()}")

# 1. 騎手ナレッジマネージャーのコード確認
print("\n1. 騎手ナレッジマネージャーのソースコード確認")
try:
    from services.jockey_knowledge_manager import JockeyKnowledgeManager
    import inspect
    
    # get_jockey_post_position_fukusho_rates メソッドのソースを確認
    method = getattr(JockeyKnowledgeManager, 'get_jockey_post_position_fukusho_rates')
    source_lines = inspect.getsourcelines(method)[0]
    
    print("get_jockey_post_position_fukusho_rates メソッドの内容:")
    for i, line in enumerate(source_lines[150:180], 151):  # 問題のある部分
        print(f"{i:3d}: {line.rstrip()}")
        
except Exception as e:
    print(f"ソースコード確認エラー: {e}")
    traceback.print_exc()

# 2. 実際のエラー再現
print("\n2. 実際のエラー再現")
try:
    from services.jockey_knowledge_manager import JockeyKnowledgeManager
    manager = JockeyKnowledgeManager()
    
    # 問題のあるメソッドを直接テスト
    test_jockeys = ['武豊', '川田', '福永']
    print(f"テスト騎手: {test_jockeys}")
    
    result = manager.get_jockey_post_position_fukusho_rates(test_jockeys)
    print(f"結果: {result}")
    print("✅ エラーなし - 修正が反映されています")
    
except Exception as e:
    print(f"❌ エラー発生: {e}")
    print(f"エラータイプ: {type(e).__name__}")
    traceback.print_exc()
    
    # エラーの詳細分析
    if "'int' object has no attribute 'get'" in str(e):
        print("\n🚨 古いコードが実行されています！")
        print("Renderのデプロイが完了していない可能性があります。")

# 3. Git情報の確認
print("\n3. 現在のGit情報")
try:
    import subprocess
    
    # 最新コミット確認
    result = subprocess.run(['git', 'log', '--oneline', '-1'], 
                          capture_output=True, text=True, cwd=os.path.dirname(__file__))
    print(f"最新コミット: {result.stdout.strip()}")
    
    # リモート同期状況
    result = subprocess.run(['git', 'status'], 
                          capture_output=True, text=True, cwd=os.path.dirname(__file__))
    print(f"Git状態: {result.stdout.strip()}")
    
except Exception as e:
    print(f"Git情報確認エラー: {e}")

# 4. ファイル更新日時確認
print("\n4. 重要ファイルの更新日時")
try:
    import datetime
    
    files_to_check = [
        'services/jockey_knowledge_manager.py',
        'services/viewlogic_engine.py',
        'main.py'
    ]
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            mtime = os.path.getmtime(file_path)
            formatted_time = datetime.datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
            print(f"{file_path}: {formatted_time}")
        else:
            print(f"{file_path}: ファイルが存在しません")
            
except Exception as e:
    print(f"ファイル日時確認エラー: {e}")

print("\n=== 調査完了 ===")