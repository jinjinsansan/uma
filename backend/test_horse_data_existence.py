#!/usr/bin/env python3
"""
ViewLogicナレッジファイル内の馬データ存在確認
"""

from services.viewlogic_data_manager import get_viewlogic_data_manager
import json

# ViewLogicデータマネージャー初期化
print("ViewLogicデータマネージャー初期化中...")
data_manager = get_viewlogic_data_manager()

# 新潟4Rの馬リスト
test_horses = [
    'ベネスティローザ',
    'ジュリスタ',
    'アンヘルカイド',
    'ミラコレジェンヌ',
    'エテオクロス',
    'ピンパンポン',
    'ピコチマチ',
    'シンフォニーシーズ',
    'マオノクラッシュ',
    'キタノライブリー',
    'ビアルベーロ',
    'セイウンヤタガラス',
    'ブライトビギニング',
    'アオイハナミチ',
    'ロドラント'
]

print(f"\nViewLogicナレッジファイル総馬数: {data_manager.get_total_horses()}頭")
print(f"データ読み込み状況: {'成功' if data_manager.is_loaded() else '失敗'}")

print(f"\n=== 新潟4R馬データ存在確認 ===")

found_horses = 0
for horse_name in test_horses:
    horse_data = data_manager.get_horse_data(horse_name)
    
    if horse_data:
        found_horses += 1
        total_races = len(horse_data.get('races', []))
        print(f"✅ {horse_name}: {total_races}戦の実績データあり")
        
        # 新潟1200m芝での実績確認
        niigata_1200_races = 0
        for race in horse_data.get('races', []):
            if (race.get('KEIBAJO_CODE') == '04' and  # 新潟
                race.get('KYORI') == 1200 and        # 1200m
                race.get('TRACK_CODE_S') == '0'):    # 芝
                niigata_1200_races += 1
        
        if niigata_1200_races > 0:
            print(f"   → 新潟1200m芝: {niigata_1200_races}戦")
        else:
            print(f"   → 新潟1200m芝: 実績なし")
    else:
        print(f"❌ {horse_name}: データなし")

print(f"\n結果: {found_horses}/{len(test_horses)}頭がViewLogicナレッジファイルに存在")
print(f"展開予想が動作する理由: 馬データ自体は存在")
print(f"傾向分析で「データなし」の理由: 新潟1200m芝での特定実績がない")