#!/usr/bin/env python3
"""騎手ナレッジファイルのデータ構造を確認"""

from services.jockey_knowledge_manager import JockeyKnowledgeManager
import json

# マネージャー初期化
manager = JockeyKnowledgeManager()

# 新潟4Rの騎手を確認
test_jockeys = [
    '菅原隆',
    '吉田豊',
    '水沼',
    '遠藤',
    '石田',
    '津村',
    '木幡巧',
    '菅原明',
    '原',
    '木幡初',
    '上里',
    '佐藤',
    '武藤',
    '団野',
    '岩部'
]

print("=== 新潟4R騎手のデータ確認 ===\n")

# 各騎手のデータを確認
for jockey in test_jockeys:
    # いろいろなパターンで検索
    patterns = [
        jockey,
        jockey + '　',  # スペース1つ
        jockey + '　　',  # スペース2つ
    ]
    
    found = False
    for pattern in patterns:
        if pattern in manager.jockey_data:
            print(f"✅ {jockey} → '{pattern}' で発見")
            found = True
            break
    
    if not found:
        # 部分一致で検索
        matches = []
        for name in manager.jockey_data.keys():
            if jockey in name:
                matches.append(name)
        
        if matches:
            print(f"⚠️ {jockey} → 部分一致: {matches}")
        else:
            print(f"❌ {jockey} → データなし")

# 吉田豊のデータを確認
print("\n=== 吉田豊の詳細データ ===")
jockey_name = '吉田豊　'  # 3文字＋スペース1つ
data = manager.get_jockey_data(jockey_name)

if data:
    print(f"騎手名: {jockey_name}")
    print(f"データキー: {data.keys()}")
    
    # 枠順別データを確認
    post_stats = data.get('post_position_stats', {})
    print(f"\n枠順別データ:")
    for waku, stats in list(post_stats.items())[:3]:
        print(f"  {waku}: {stats}")
    
    # 内枠での成績を集計
    inner_total = 0
    inner_fukusho = 0
    for waku_str, stats in post_stats.items():
        try:
            waku_num = int(waku_str.replace('枠', ''))
            if 1 <= waku_num <= 6:
                race_count = stats.get('race_count', 0)
                fukusho_rate = stats.get('fukusho_rate', 0)
                print(f"  {waku_str}: {race_count}戦, 複勝率{fukusho_rate}")
                inner_total += race_count
                # 複勝数を計算
                inner_fukusho += race_count * fukusho_rate
        except:
            continue
    
    if inner_total > 0:
        avg_rate = inner_fukusho / inner_total
        print(f"\n内枠合計: {inner_total}戦, 平均複勝率{avg_rate:.3f}")
else:
    print(f"騎手データが見つかりません: {jockey_name}")

# 騎手名一覧を確認
print(f"\n騎手総数: {manager.get_total_jockeys()}")

# 吉田を含む騎手を検索
print("\n吉田を含む騎手:")
for name in manager.jockey_data.keys():
    if '吉田' in name:
        print(f"  '{name}' (長さ: {len(name)})")

print("\n騎手名サンプル（最初の10名）:")
for name in list(manager.jockey_data.keys())[:10]:
    print(f"  '{name}' (長さ: {len(name)})")

# 正確な騎手名を確認
print("\n=== 特定騎手の正確な名前 ===")
target_names = ['菅原隆一', '水沼元輝', '津村明秀', '団野大成', '岩部純二']
for target in target_names:
    if target in manager.jockey_data:
        print(f"✅ '{target}' が存在")
        # 枠順データを確認
        post_stats = manager.get_post_position_stats(target)
        if post_stats:
            print(f"   枠順データあり（{len(post_stats)}枠分）")
    else:
        print(f"❌ '{target}' が存在しない")