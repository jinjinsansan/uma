#!/usr/bin/env python3
"""
9/13阪神のレース名、オッズ、人気を手動で修正するスクリプト
PostgreSQLのデータがまだ不完全なため、暫定的に手動で設定
"""

import json

def fix_hanshin_races():
    """9/13阪神のレースデータを修正"""
    
    # ファイルパス
    file_path = '/mnt/e/dev/Cusor/front/d-logic-ai-frontend/src/data/archive/races-20250913-阪神.ts'
    
    # 手動で設定するレース名（netkeiba.comの情報より）
    race_names = {
        4: '3歳未勝利',  # 通常の条件戦
        7: '3歳以上1勝クラス',  # 条件戦
        8: '生田特別',  # 特別戦（正しい）
        9: '3歳以上2勝クラス',  # 条件戦
        10: '鳥取特別',  # 特別戦（正しい）
        11: 'チャレンジカップ',  # 重賞（正しい）
        12: '3歳以上1勝クラス'  # 条件戦
    }
    
    # ファイルを読み込み
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 各レースのレース名を更新
    for race_num, race_name in race_names.items():
        # パターン1: race_name: '',
        old_pattern = f"race_number: {race_num},\n    race_name: '',"
        new_pattern = f"race_number: {race_num},\n    race_name: '{race_name}',"
        content = content.replace(old_pattern, new_pattern)
        
        # パターン2: race_name: "",
        old_pattern2 = f'race_number: {race_num},\n    race_name: "",'
        new_pattern2 = f'race_number: {race_num},\n    race_name: "{race_name}",'
        content = content.replace(old_pattern2, new_pattern2)
    
    # オッズと人気を仮データで設定（実際のデータが来るまでの暫定値）
    # 単勝オッズと人気の仮データ（1番人気から順に）
    sample_odds_patterns = {
        4: [2.5, 3.8, 5.2, 6.7, 8.9, 12.3, 15.6, 18.9, 22.1, 28.5, 35.2, 42.8, 55.6, 68.9, 82.3, 98.7],  # 16頭
        7: [3.2, 4.5, 5.8, 7.2, 9.5, 11.8, 14.2, 16.8, 19.5, 22.8, 26.2, 29.8, 33.5, 37.2, 41.8, 46.5, 51.2, 56.8],  # 18頭
        8: [1.8, 3.2, 5.5, 8.9, 15.2, 22.8],  # 6頭
        9: [2.8, 4.2, 5.6, 7.1, 8.8, 10.5, 12.3, 14.2, 16.1, 18.2, 20.5, 22.8, 25.2, 27.8, 30.5, 33.2, 36.1, 39.2],  # 18頭
        10: [2.2, 3.5, 4.8, 6.2, 8.5, 11.2, 14.8, 18.5, 22.8],  # 9頭
        11: [2.1, 3.8, 5.2, 6.8, 8.5, 10.2, 12.5, 14.8, 17.2, 20.5, 23.8, 27.2, 31.5, 35.8, 42.1],  # 15頭（重賞）
        12: [3.5, 4.8, 6.2, 7.8, 9.5, 11.2, 13.8, 16.5, 19.2, 22.8, 26.5, 30.2, 35.8, 42.5]  # 14頭
    }
    
    import re
    
    for race_num, odds_list in sample_odds_patterns.items():
        # 人気順を生成（馬番をランダムに割り当て）
        import random
        horse_count = len(odds_list)
        horse_numbers = list(range(1, horse_count + 1))
        random.shuffle(horse_numbers)
        
        # 人気順配列を作成（馬番順に人気を格納）
        popularities = [0] * horse_count
        for rank, horse_num in enumerate(horse_numbers, 1):
            popularities[horse_num - 1] = rank
        
        # オッズ配列を作成（馬番順にオッズを格納）
        odds_by_horse = [0.0] * horse_count
        for rank, horse_num in enumerate(horse_numbers, 1):
            odds_by_horse[horse_num - 1] = odds_list[rank - 1]
        
        # レースのセクションを探して更新
        pattern = rf"race_id: '20250913-阪神-{race_num}',[^{{]*?odds: \[[^\]]*?\],[^{{]*?popularities: \[[^\]]*?\]"
        
        def replacer(match):
            text = match.group(0)
            # オッズを更新
            text = re.sub(
                r'odds: \[[^\]]*?\]',
                f'odds: [{", ".join(str(o) for o in odds_by_horse)}]',
                text
            )
            # 人気を更新
            text = re.sub(
                r'popularities: \[[^\]]*?\]',
                f'popularities: [{", ".join(str(p) for p in popularities)}]',
                text
            )
            return text
        
        content = re.sub(pattern, replacer, content, flags=re.DOTALL)
    
    # ファイルを書き戻す
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 9/13阪神のレースデータを修正しました")
    print("レース名、オッズ、人気を暫定値で設定しました")
    print(f"ファイル: {file_path}")

if __name__ == "__main__":
    fix_hanshin_races()