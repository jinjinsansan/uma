#!/usr/bin/env python3
"""
自動実行用バッチランナー（対話プロンプト回避）
"""
import subprocess
import sys

print("🚀 D-Logic生データナレッジ自動構築開始")
print("📊 現在: 8,400頭 → 目標: 約50,000頭")
print("⏱️ 推定時間: 2-4時間")
print("")

# 環境変数で自動実行モード設定
import os
os.environ['AUTO_BATCH'] = 'yes'

# バッチ実行
try:
    subprocess.run([sys.executable, 'batch_create_raw_knowledge.py'], 
                   input='yes\n', text=True, check=True)
except Exception as e:
    print(f"エラー: {e}")
    # 堅牢版を試行
    print("堅牢版バッチを実行します...")
    subprocess.run([sys.executable, 'batch_robust_knowledge_builder.py'])