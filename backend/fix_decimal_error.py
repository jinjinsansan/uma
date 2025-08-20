#!/usr/bin/env python3
"""
騎手ナレッジファイル作成 - Decimal型エラー修正版
Decimal型のJSON変換エラーを修正して処理を再開

2025-08-20 作成
"""
import json
import re
from datetime import datetime
from decimal import Decimal

def fix_decimal_json_error():
    """
    Decimal型エラーを修正してcreate_extended_jockey_knowledge_v2.pyを更新
    """
    input_file = "/mnt/c/Users/USER/OneDrive/デスクトップ/Cusor/chatbot/uma/backend/create_extended_jockey_knowledge_v2.py"
    
    print("🔧 Decimal型エラー修正中...")
    
    # ファイルを読み込み
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # DecimalEncoderクラスを追加
    decimal_encoder_code = '''import json
import logging
import os
import sys
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Any
import mysql.connector

# JSON用Decimalエンコーダー
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)

'''
    
    # 既存のimport文をDecimalEncoder付きで置換
    content = re.sub(
        r'import json\nimport logging.*?import mysql\.connector',
        decimal_encoder_code.strip(),
        content,
        flags=re.DOTALL
    )
    
    # json.dump呼び出しにDecimalEncoderを追加
    content = content.replace(
        'json.dump(self.jockey_data, f, ensure_ascii=False, indent=2)',
        'json.dump(self.jockey_data, f, ensure_ascii=False, indent=2, cls=DecimalEncoder)'
    )
    
    # 最終保存のjson.dumpも修正
    content = content.replace(
        'json.dump(final_data, f, ensure_ascii=False, indent=2)',
        'json.dump(final_data, f, ensure_ascii=False, indent=2, cls=DecimalEncoder)'
    )
    
    # バックアップ作成
    backup_file = input_file + '.backup_' + datetime.now().strftime('%Y%m%d_%H%M%S')
    with open(backup_file, 'w', encoding='utf-8') as f:
        f.write(open(input_file, 'r', encoding='utf-8').read())
    
    # 修正版を保存
    with open(input_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ 修正完了:")
    print(f"   - 元ファイル: {input_file}")
    print(f"   - バックアップ: {backup_file}")
    print(f"   - DecimalEncoderクラス追加")
    print(f"   - json.dump呼び出し2箇所を修正")
    
    return True

def restart_processing_from_50():
    """
    50番目の騎手（コレット）から処理を再開
    """
    print("\n🔄 処理再開の準備:")
    print("1. 修正されたスクリプトで処理再開")
    print("2. 既存の進捗ファイルから継続")
    print("3. 残り756名の騎手を処理")
    
    restart_cmd = """
# WSLターミナルで実行:
cd /mnt/c/Users/USER/OneDrive/デスクトップ/Cusor/chatbot/uma/backend
nohup python3 create_extended_jockey_knowledge_v2.py > extended_jockey_process_fixed.log 2>&1 &

# 進捗確認:
tail -f extended_jockey_process_fixed.log
"""
    
    print(restart_cmd)
    return restart_cmd

if __name__ == "__main__":
    print("🏇 騎手ナレッジファイル - Decimal型エラー修正ツール")
    print("=" * 50)
    
    # エラー修正
    fix_decimal_json_error()
    
    # 再開手順
    restart_processing_from_50()
    
    print("\n📋 修正内容サマリー:")
    print("- Decimal型 → float型に自動変換するエンコーダー追加")
    print("- JSON保存時のエラーを解決")
    print("- 50番目から処理を再開可能")
    print("- 推定残り時間: 約19時間（756名 × 1.5分/名）")