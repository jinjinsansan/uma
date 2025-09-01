#!/usr/bin/env python3
"""
スタイルインデックスの値を詳しく確認
"""

from services.viewlogic_engine import ViewLogicEngine

def debug_style_index():
    """スタイルインデックスの詳細を確認"""
    
    engine = ViewLogicEngine()
    
    test_horses = ['バッキンガムパレス', 'ヴィジブルライト', 'サトノアルタイル', 
                   'ドウデュース', 'イクイノックス']
    
    print("=== スタイルインデックスの詳細確認 ===\n")
    
    for horse_name in test_horses:
        horse_data = engine.data_manager.get_horse_data(horse_name)
        if horse_data and 'races' in horse_data:
            races = horse_data['races'][:5]  # 直近5レース
            
            print(f"\n【{horse_name}】")
            print("レース別のデータ:")
            
            valid_count = 0
            for i, race in enumerate(races, 1):
                zenhan_raw = race.get('ZENHAN_3F')
                kohan_raw = race.get('KOHAN_3F')
                
                if zenhan_raw and kohan_raw:
                    zenhan = engine._normalize_3f_time(float(zenhan_raw))
                    kohan = engine._normalize_3f_time(float(kohan_raw))
                    
                    if zenhan and kohan:
                        diff = kohan - zenhan
                        valid_count += 1
                        print(f"  レース{i}: 前半{zenhan:.1f}秒, 後半{kohan:.1f}秒, 差={diff:.1f}秒")
                    else:
                        print(f"  レース{i}: データ欠損")
                else:
                    print(f"  レース{i}: データなし")
            
            # スタイルインデックスを計算
            if 'races' in horse_data:
                style_index = engine._calculate_style_index(races)
                print(f"\n最終スタイルインデックス: {style_index:.2f}")
                print(f"データ有効レース数: {valid_count}/5")
                
                # ペースによるスコア計算例
                print("\n展開マッチングスコア:")
                for pace in ['ハイペース', 'スローペース', '平均ペース']:
                    base_score = 60.0
                    if 'ハイペース' in pace:
                        if style_index > 0:
                            score = base_score * 1.2
                        else:
                            score = base_score * 0.85
                    elif 'スローペース' in pace:
                        if style_index < 0:
                            score = base_score * 1.15
                        else:
                            score = base_score * 0.9
                    else:
                        adjustment = (5 - abs(style_index)) * 3
                        score = base_score + adjustment
                    
                    final_score = min(85, max(40, score))
                    print(f"  {pace}: {final_score:.1f}点")

if __name__ == "__main__":
    debug_style_index()