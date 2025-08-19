#!/usr/bin/env python3
"""
騎手ナレッジファイルの構造と内容を確認
"""
import os
import sys
import json
from pathlib import Path

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_jockey_knowledge():
    """騎手ナレッジファイルの詳細を確認"""
    print("=== 騎手ナレッジファイル構造確認 ===\n")
    
    # ファイルパス
    data_dir = Path(__file__).parent / "data"
    knowledge_file = data_dir / "jockey_knowledge.json"
    
    if not knowledge_file.exists():
        print(f"❌ ファイルが存在しません: {knowledge_file}")
        return
    
    # ファイル読み込み
    with open(knowledge_file, 'r', encoding='utf-8') as f:
        jockey_data = json.load(f)
    
    print(f"1. 基本情報:")
    print(f"   総騎手数: {len(jockey_data)}")
    
    # サンプル騎手で構造確認
    sample_jockeys = ['武豊', 'C.ルメール', 'ルメール', '川端', '江田照', '江田照男', '川端海弥']
    
    print(f"\n2. 騎手名の検索:")
    for jockey in sample_jockeys:
        if jockey in jockey_data:
            print(f"   ✅ {jockey}: 存在する")
        else:
            print(f"   ❌ {jockey}: 存在しない")
    
    # 騎手名一覧（一部）を表示
    print(f"\n3. 騎手名サンプル（最初の20名）:")
    for i, name in enumerate(list(jockey_data.keys())[:20]):
        print(f"   {i+1:2d}. {name}")
    
    # データ構造の確認
    print(f"\n4. データ構造の確認（武豊の例）:")
    if '武豊' in jockey_data:
        takeyutaka_data = jockey_data['武豊']
        print(f"   キー: {list(takeyutaka_data.keys())}")
        
        # sire_statsの確認
        if 'sire_stats' in takeyutaka_data:
            sire_count = len(takeyutaka_data['sire_stats'])
            print(f"   種牡馬データ数: {sire_count}")
            if sire_count > 0:
                # 最初の5つを表示
                for i, (sire, stats) in enumerate(list(takeyutaka_data['sire_stats'].items())[:5]):
                    print(f"     - {sire}: {stats.get('total_races', 0)}戦, 複勝率{stats.get('fukusho_rate', 0)}%")
        else:
            print(f"   種牡馬データ: なし")
    
    # 「川」や「江田」を含む騎手名を検索
    print(f"\n5. 部分一致検索:")
    print(f"   '川'を含む騎手:")
    kawa_jockeys = [name for name in jockey_data.keys() if '川' in name]
    for name in kawa_jockeys[:10]:  # 最初の10名
        print(f"     - {name}")
    
    print(f"\n   '江田'を含む騎手:")
    eda_jockeys = [name for name in jockey_data.keys() if '江田' in name]
    for name in eda_jockeys[:10]:  # 最初の10名
        print(f"     - {name}")
    
    print(f"\n   'ルメール'を含む騎手:")
    lemaire_jockeys = [name for name in jockey_data.keys() if 'ルメール' in name]
    for name in lemaire_jockeys:
        print(f"     - {name}")

if __name__ == "__main__":
    check_jockey_knowledge()