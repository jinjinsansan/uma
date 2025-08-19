#!/usr/bin/env python3
"""
騎手ナレッジファイルの名前パターンを分析し、
netkeiba形式（3文字省略）との対応を調査
"""
import json
from pathlib import Path
import re

def analyze_jockey_names():
    """騎手名のパターンを分析"""
    print("=== 騎手名パターン分析 ===\n")
    
    # ファイル読み込み
    data_dir = Path(__file__).parent / "data"
    knowledge_file = data_dir / "jockey_knowledge.json"
    
    with open(knowledge_file, 'r', encoding='utf-8') as f:
        jockey_data = json.load(f)
    
    # 名前の分析
    all_names = list(jockey_data.keys())
    
    # パターン別に分類
    patterns = {
        '2文字': [],
        '3文字': [],
        '4文字': [],
        '5文字以上': [],
        '外国人（カナ）': [],
        '外国人（英字）': [],
        'スペース含む': []
    }
    
    for name in all_names:
        # スペースを除去した長さ
        clean_name = name.strip().strip('　')
        
        if name != clean_name:
            patterns['スペース含む'].append(f"{name} (→{clean_name})")
        
        # 外国人騎手の判定
        if re.search(r'[A-Za-z．]', clean_name):
            patterns['外国人（英字）'].append(clean_name)
        elif re.search(r'[ァ-ヴー]{3,}', clean_name) and '・' not in clean_name:
            # カタカナが3文字以上続く
            patterns['外国人（カナ）'].append(clean_name)
        else:
            # 日本人騎手
            if len(clean_name) == 2:
                patterns['2文字'].append(clean_name)
            elif len(clean_name) == 3:
                patterns['3文字'].append(clean_name)
            elif len(clean_name) == 4:
                patterns['4文字'].append(clean_name)
            else:
                patterns['5文字以上'].append(clean_name)
    
    # 結果表示
    print("1. 名前の長さ別分類:")
    for pattern, names in patterns.items():
        if pattern != 'スペース含む':
            print(f"\n{pattern}: {len(names)}名")
            # サンプル表示
            for name in sorted(names)[:10]:
                print(f"  - {name}")
            if len(names) > 10:
                print(f"  ... 他{len(names)-10}名")
    
    # スペース問題の詳細
    print("\n2. スペース問題の詳細:")
    space_names = patterns['スペース含む']
    print(f"スペースを含む騎手: {len(space_names)}名")
    for name in space_names[:20]:
        print(f"  - {name}")
    
    # netkeiba形式への変換ルール提案
    print("\n3. netkeiba形式（3文字）への変換ルール:")
    print("\n【4文字騎手の例】")
    four_char_names = [n for n in all_names if len(n.strip().strip('　')) == 4]
    
    # 横山系
    yokoyama_names = [n for n in four_char_names if n.startswith('横山')]
    print("\n横山系:")
    for name in sorted(yokoyama_names):
        clean = name.strip().strip('　')
        netkeiba_form = clean[:2] + clean[3] if len(clean) >= 4 else clean
        print(f"  {clean} → {netkeiba_form}")
    
    # 吉田系
    yoshida_names = [n for n in four_char_names if n.startswith('吉田')]
    print("\n吉田系:")
    for name in sorted(yoshida_names):
        clean = name.strip().strip('　')
        netkeiba_form = clean[:2] + clean[3] if len(clean) >= 4 else clean
        print(f"  {clean} → {netkeiba_form}")
    
    # その他の4文字
    print("\nその他の4文字騎手（サンプル）:")
    other_four = [n for n in four_char_names if not (n.startswith('横山') or n.startswith('吉田'))]
    for name in sorted(other_four)[:20]:
        clean = name.strip().strip('　')
        netkeiba_form = clean[:2] + clean[3] if len(clean) >= 4 else clean
        print(f"  {clean} → {netkeiba_form}")

if __name__ == "__main__":
    analyze_jockey_names()