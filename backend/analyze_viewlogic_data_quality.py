#!/usr/bin/env python3
"""
ViewLogicナレッジファイルのデータ品質を詳細分析
"""

from services.viewlogic_data_manager import get_viewlogic_data_manager
import json
from collections import Counter

def analyze_data_quality():
    """データ品質の詳細分析"""
    
    # データマネージャーを取得
    manager = get_viewlogic_data_manager()
    
    print("=== ViewLogicナレッジファイル データ品質分析 ===\n")
    
    total_horses = manager.get_total_horses()
    print(f"【総馬数】: {total_horses:,}頭\n")
    
    # 統計情報を収集
    stats = {
        'has_zenhan_kohan': 0,  # 前半3F・後半3F両方あり
        'has_zenhan_only': 0,   # 前半3Fのみ
        'has_kohan_only': 0,    # 後半3Fのみ
        'no_data': 0,           # 両方なし
        'has_races': 0,         # レースデータあり
        'no_races': 0,          # レースデータなし
        'zenhan_values': [],    # 前半3Fの値（0以外）
        'kohan_values': [],     # 後半3Fの値（0以外）
        'races_per_horse': [],  # 馬ごとのレース数
        'valid_races_per_horse': [],  # 有効データがあるレース数
    }
    
    # 値の分布を調査
    zenhan_distribution = Counter()
    kohan_distribution = Counter()
    
    # サンプル馬（データありとなし）
    sample_with_data = []
    sample_without_data = []
    
    # 全馬をチェック
    for horse_name, horse_data in manager.horses_dict.items():
        if 'races' not in horse_data or not horse_data['races']:
            stats['no_races'] += 1
            sample_without_data.append(horse_name)
            continue
        
        stats['has_races'] += 1
        races = horse_data['races']
        stats['races_per_horse'].append(len(races))
        
        # 各馬の有効レース数をカウント
        valid_races = 0
        horse_has_zenhan = False
        horse_has_kohan = False
        
        for race in races:
            zenhan = race.get('ZENHAN_3F', 0)
            kohan = race.get('KOHAN_3F', 0)
            
            # 値の分布を記録
            if zenhan > 0:
                zenhan_distribution[int(zenhan)] += 1
                stats['zenhan_values'].append(zenhan)
                horse_has_zenhan = True
                
            if kohan > 0:
                kohan_distribution[int(kohan)] += 1
                stats['kohan_values'].append(kohan)
                horse_has_kohan = True
                
            if zenhan > 0 or kohan > 0:
                valid_races += 1
        
        stats['valid_races_per_horse'].append(valid_races)
        
        # 馬ごとの統計
        if horse_has_zenhan and horse_has_kohan:
            stats['has_zenhan_kohan'] += 1
            if len(sample_with_data) < 5:
                sample_with_data.append(horse_name)
        elif horse_has_zenhan:
            stats['has_zenhan_only'] += 1
        elif horse_has_kohan:
            stats['has_kohan_only'] += 1
        else:
            stats['no_data'] += 1
            if len(sample_without_data) < 5:
                sample_without_data.append(horse_name)
    
    # 結果を表示
    print("【データ保有状況】")
    print(f"前半3F・後半3F両方あり: {stats['has_zenhan_kohan']:,}頭 ({stats['has_zenhan_kohan']/total_horses*100:.1f}%)")
    print(f"前半3Fのみ: {stats['has_zenhan_only']:,}頭 ({stats['has_zenhan_only']/total_horses*100:.1f}%)")
    print(f"後半3Fのみ: {stats['has_kohan_only']:,}頭 ({stats['has_kohan_only']/total_horses*100:.1f}%)")
    print(f"両方なし: {stats['no_data']:,}頭 ({stats['no_data']/total_horses*100:.1f}%)")
    print(f"レースデータなし: {stats['no_races']:,}頭 ({stats['no_races']/total_horses*100:.1f}%)")
    print()
    
    # レース数の統計
    if stats['races_per_horse']:
        avg_races = sum(stats['races_per_horse']) / len(stats['races_per_horse'])
        max_races = max(stats['races_per_horse'])
        min_races = min(stats['races_per_horse'])
        print("【レース数統計】")
        print(f"平均レース数: {avg_races:.1f}レース/頭")
        print(f"最大レース数: {max_races}レース")
        print(f"最小レース数: {min_races}レース")
        print()
    
    # 有効レース数の統計
    if stats['valid_races_per_horse']:
        valid_races_with_data = [x for x in stats['valid_races_per_horse'] if x > 0]
        if valid_races_with_data:
            avg_valid = sum(valid_races_with_data) / len(valid_races_with_data)
            print("【有効データがあるレース数】")
            print(f"有効データがある馬: {len(valid_races_with_data):,}頭")
            print(f"平均有効レース数: {avg_valid:.1f}レース/頭")
            print()
    
    # 値の範囲を確認
    if stats['zenhan_values']:
        print("【前半3Fの値の分布】")
        print(f"データ数: {len(stats['zenhan_values']):,}個")
        print(f"最小値: {min(stats['zenhan_values']):.1f} → {min(stats['zenhan_values'])/10:.1f}秒")
        print(f"最大値: {max(stats['zenhan_values']):.1f} → {max(stats['zenhan_values'])/10:.1f}秒")
        avg_zenhan = sum(stats['zenhan_values']) / len(stats['zenhan_values'])
        print(f"平均値: {avg_zenhan:.1f} → {avg_zenhan/10:.1f}秒")
        
        # 値の範囲別分布
        ranges = {
            '30秒台前半(300-339)': 0,
            '30秒台後半(340-369)': 0,
            '40秒台(370-399)': 0,
            '40秒以上(400+)': 0,
            '異常値(300未満)': 0
        }
        
        for val in stats['zenhan_values']:
            if val < 300:
                ranges['異常値(300未満)'] += 1
            elif val < 340:
                ranges['30秒台前半(300-339)'] += 1
            elif val < 370:
                ranges['30秒台後半(340-369)'] += 1
            elif val < 400:
                ranges['40秒台(370-399)'] += 1
            else:
                ranges['40秒以上(400+)'] += 1
        
        print("\n値の範囲別分布:")
        for range_name, count in ranges.items():
            if count > 0:
                print(f"  {range_name}: {count:,}個 ({count/len(stats['zenhan_values'])*100:.1f}%)")
        print()
    
    if stats['kohan_values']:
        print("【後半3Fの値の分布】")
        print(f"データ数: {len(stats['kohan_values']):,}個")
        print(f"最小値: {min(stats['kohan_values']):.1f} → {min(stats['kohan_values'])/10:.1f}秒")
        print(f"最大値: {max(stats['kohan_values']):.1f} → {max(stats['kohan_values'])/10:.1f}秒")
        avg_kohan = sum(stats['kohan_values']) / len(stats['kohan_values'])
        print(f"平均値: {avg_kohan:.1f} → {avg_kohan/10:.1f}秒")
        print()
    
    # サンプル表示
    print("【サンプル馬（データあり）】")
    for horse in sample_with_data[:5]:
        print(f"  - {horse}")
    print()
    
    print("【サンプル馬（データなし）】")
    for horse in sample_without_data[:5]:
        print(f"  - {horse}")
    
    # 最も多い値を確認
    print("\n【最頻値TOP10】")
    print("前半3F:")
    for val, count in zenhan_distribution.most_common(10):
        if val > 0:
            print(f"  {val} ({val/10:.1f}秒): {count}回")
    
    print("\n後半3F:")
    for val, count in kohan_distribution.most_common(10):
        if val > 0:
            print(f"  {val} ({val/10:.1f}秒): {count}回")

if __name__ == "__main__":
    analyze_data_quality()