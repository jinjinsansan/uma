#!/usr/bin/env python3
"""
データ形式の混在問題を詳しく調査
"""

from services.viewlogic_data_manager import get_viewlogic_data_manager

def investigate_format():
    """データ形式の詳細調査"""
    
    manager = get_viewlogic_data_manager()
    
    print("=== データ形式の詳細調査 ===\n")
    
    # 異なる形式のサンプルを収集
    samples = {
        'format_01sec': [],  # 0.1秒単位（300以上）
        'format_sec': [],    # 秒単位（100未満）
        'format_unknown': [] # 不明（100-299）
    }
    
    checked = 0
    for horse_name, horse_data in manager.horses_dict.items():
        if checked >= 100:  # 最初の100頭をチェック
            break
        
        if 'races' in horse_data and horse_data['races']:
            for race in horse_data['races'][:1]:  # 最新レースのみ
                zenhan = race.get('ZENHAN_3F', 0)
                kohan = race.get('KOHAN_3F', 0)
                
                if zenhan > 0:
                    # データ形式を判定
                    if zenhan >= 300:
                        format_type = 'format_01sec'
                        actual_time = zenhan / 10
                    elif zenhan < 100:
                        format_type = 'format_sec'
                        actual_time = zenhan
                    else:
                        format_type = 'format_unknown'
                        actual_time = zenhan
                    
                    samples[format_type].append({
                        'horse': horse_name,
                        'raw_zenhan': zenhan,
                        'raw_kohan': kohan,
                        'actual_zenhan': actual_time,
                        'actual_kohan': kohan / 10 if kohan >= 300 else kohan
                    })
                    checked += 1
                    break
    
    # 結果を表示
    print("【データ形式の分類】\n")
    
    print("1. 0.1秒単位形式（300以上）:")
    for sample in samples['format_01sec'][:5]:
        print(f"  {sample['horse']}: 前半3F={sample['raw_zenhan']} → {sample['actual_zenhan']:.1f}秒")
    print(f"  計: {len(samples['format_01sec'])}件\n")
    
    print("2. 秒単位形式（100未満）:")
    for sample in samples['format_sec'][:5]:
        print(f"  {sample['horse']}: 前半3F={sample['raw_zenhan']} → {sample['actual_zenhan']:.1f}秒")
    print(f"  計: {len(samples['format_sec'])}件\n")
    
    print("3. 不明形式（100-299）:")
    for sample in samples['format_unknown'][:5]:
        print(f"  {sample['horse']}: 前半3F={sample['raw_zenhan']} → ???")
    print(f"  計: {len(samples['format_unknown'])}件\n")
    
    # 統計
    total = len(samples['format_01sec']) + len(samples['format_sec']) + len(samples['format_unknown'])
    print("【形式別の割合】")
    print(f"0.1秒単位: {len(samples['format_01sec'])/total*100:.1f}%")
    print(f"秒単位: {len(samples['format_sec'])/total*100:.1f}%")
    print(f"不明: {len(samples['format_unknown'])/total*100:.1f}%")

if __name__ == "__main__":
    investigate_format()